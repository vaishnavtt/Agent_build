"""LangGraph orchestration for one recovery invocation."""

import json
from dataclasses import dataclass, field, replace
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from langsmith import tracing_context
from typing_extensions import TypedDict

from app.schemas.repair import (
    MAX_AUTOMATIC_REPAIR_ATTEMPTS,
    FailureCategory,
    RollbackStatus,
    VerificationResult,
    VerificationStatus,
)
from app.services.repair.diagnosis_router import DiagnosisOutcome, DiagnosisRouter, DiagnosisStatus
from app.services.repair.planning import RepairPlan, RepairPlanner, UnsafeRepair
from app.services.repair.recovery_contracts import (
    AttemptStatus,
    CandidateEvidence,
    ProposalReference,
    RecoveryAttempt,
    RecoveryRecorder,
    RecoveryRequest,
    RecoveryResult,
    RecoveryStatus,
    RecoveryVerification,
    RetryStopReason,
    RevisionConflict,
    RevisionLifecycle,
    RevisionReference,
    RevisionUpdate,
    SnapshotSource,
    VerificationBaseline,
)
from app.services.repair.service import WorkflowSnapshot

RECOVERY_RECURSION_LIMIT = 32


class RecoveryState(TypedDict, total=False):
    original: RevisionReference
    execution_run_id: str
    diagnosis: DiagnosisOutcome
    repair_eligible: bool
    snapshot: RevisionReference
    proposal: ProposalReference
    candidate: RevisionReference | None
    attempt_count: int
    attempts: tuple[RecoveryAttempt, ...]
    verification: VerificationResult | None
    decision: VerificationStatus
    promotion: RevisionUpdate
    rollback: RollbackStatus
    restored_revision: RevisionReference
    retry_stop: RetryStopReason
    status: RecoveryStatus
    explanation: str
    route: str
    result: RecoveryResult


@dataclass
class _RunData:
    request: RecoveryRequest
    snapshot: WorkflowSnapshot | None = None
    plan: RepairPlan | None = None
    attempted_plans: list[RepairPlan] = field(default_factory=list)
    candidate: WorkflowSnapshot | None = None
    baseline: VerificationBaseline | None = None
    evidence: CandidateEvidence | None = None


class RecoveryGraph:
    def __init__(
        self,
        router: DiagnosisRouter,
        planner: RepairPlanner,
        snapshots: SnapshotSource,
        *,
        verifier: RecoveryVerification | None = None,
        lifecycle: RevisionLifecycle | None = None,
        recorder: RecoveryRecorder | None = None,
    ) -> None:
        self._router = router
        self._planner = planner
        self._snapshots = snapshots
        self._verifier = verifier
        self._lifecycle = lifecycle
        self._recorder = recorder
        self.graph = self._compile()

    def _compile(self):
        graph = StateGraph(RecoveryState, context_schema=_RunData)
        nodes = {
            "validate_context": self._validate_context,
            "diagnose": self._diagnose,
            "check_eligibility": self._check_eligibility,
            "preserve_snapshot": self._preserve_snapshot,
            "plan": self._plan,
            "reserve_attempt": self._reserve_attempt,
            "apply_candidate": self._apply_candidate,
            "verify_candidate": self._verify_candidate,
            "evaluate_evidence": self._evaluate_evidence,
            "decide": self._decide,
            "promote": self._promote,
            "rollback": self._rollback,
            "finalize": self._finalize,
        }
        for name, node in nodes.items():
            graph.add_node(name, node)
        graph.add_edge(START, "validate_context")
        graph.add_edge("diagnose", "check_eligibility")
        graph.add_edge("verify_candidate", "evaluate_evidence")
        graph.add_edge("evaluate_evidence", "decide")
        for origin, destinations in {
            "validate_context": ("diagnose", "finalize"),
            "check_eligibility": ("preserve_snapshot", "finalize"),
            "preserve_snapshot": ("plan", "finalize"),
            "plan": ("reserve_attempt", "rollback", "finalize"),
            "reserve_attempt": ("apply_candidate", "rollback"),
            "apply_candidate": ("verify_candidate", "finalize"),
            "decide": ("promote", "plan", "rollback", "finalize"),
        }.items():
            graph.add_conditional_edges(origin, _route, list(destinations))
        graph.add_edge("promote", "finalize")
        graph.add_edge("rollback", "finalize")
        graph.add_edge("finalize", END)
        return graph.compile()

    def recover(self, request: RecoveryRequest) -> RecoveryResult:
        failure = request.failure
        state: RecoveryState = {
            "original": RevisionReference(failure.workflow_id, failure.workflow_revision_id),
            "execution_run_id": failure.execution_run_id,
            "attempt_count": 0,
            "attempts": (),
        }
        try:
            with tracing_context(enabled=False):
                for state in self.graph.stream(
                    state, context=_RunData(request),
                    config={"recursion_limit": RECOVERY_RECURSION_LIMIT},
                    stream_mode="values",
                ):
                    pass
            return state["result"]
        except Exception:
            # Keep committed graph updates, including any confirmed lifecycle outcome.
            if "status" not in state:
                reason = "The recovery graph stopped unexpectedly."
                state.update(_finish(RecoveryStatus.GRAPH_ERROR, reason))
                if state["attempts"] and state["attempts"][-1].status == AttemptStatus.STARTED:
                    state.update(_update_attempt(state, status=AttemptStatus.INTERRUPTED, explanation=reason))
            return self._finalize(state)["result"]

    def _validate_context(self, state: RecoveryState, runtime: Runtime[_RunData]) -> RecoveryState:
        failure, context = runtime.context.request.failure, runtime.context.request.context
        if context is None or (
            context.workflow_id != failure.workflow_id
            or context.workflow_revision_id != failure.workflow_revision_id
            or context.execution_run_id != failure.execution_run_id
        ):
            return _finish(RecoveryStatus.INVALID_CONTEXT, "Trusted context does not match the failed run and revision.")
        node_id = failure.failed_node_id
        if node_id is not None and sum(node.node_id == node_id for node in context.nodes) != 1:
            return _finish(RecoveryStatus.INVALID_CONTEXT, "The failed node ID does not identify exactly one node.")
        if context.configuration_evidence is not None and context.configuration_evidence.node_id != node_id:
            return _finish(RecoveryStatus.INVALID_CONTEXT, "The field evidence conflicts with the failed node.")
        return {"route": "diagnose"}

    def _diagnose(self, state: RecoveryState, runtime: Runtime[_RunData]) -> RecoveryState:
        request = runtime.context.request
        return {"diagnosis": self._router.diagnose_with_details(
            request.failure, request.requirements, context=request.context
        )}

    def _check_eligibility(self, state: RecoveryState) -> RecoveryState:
        outcome = state["diagnosis"]
        diagnosis = outcome.deterministic
        if (
            outcome.status == DiagnosisStatus.DETERMINISTIC
            and diagnosis.repairable
            and not diagnosis.requires_human_intervention
        ):
            return {"repair_eligible": True, "route": "preserve_snapshot"}
        if outcome.advisory is not None or (
            diagnosis.requires_human_intervention and diagnosis.category != FailureCategory.UNKNOWN
        ):
            return {"repair_eligible": False, **_finish(
                RecoveryStatus.HUMAN_REVIEW, "The diagnosis requires human review before changes can be made."
            )}
        return {"repair_eligible": False, **_finish(
            RecoveryStatus.UNRESOLVED, "Trusted evidence did not establish an eligible automatic repair."
        )}

    def _preserve_snapshot(self, state: RecoveryState, runtime: Runtime[_RunData]) -> RecoveryState:
        original = state["original"]
        try:
            snapshot = self._snapshots.save_snapshot(original.workflow_id, original.revision_id)
        except RevisionConflict:
            return _finish(RecoveryStatus.REVISION_CONFLICT, "The original revision is no longer current.")
        except Exception:
            return _finish(RecoveryStatus.SNAPSHOT_UNAVAILABLE, "The original snapshot could not be obtained.")
        if snapshot is None:
            return _finish(RecoveryStatus.SNAPSHOT_UNAVAILABLE, "The original snapshot is unavailable.")
        if _reference(snapshot) != original:
            return _finish(RecoveryStatus.REVISION_CONFLICT, "The snapshot does not match the original revision.")
        runtime.context.snapshot = snapshot
        return {"snapshot": original, "route": "plan"}

    def _plan(self, state: RecoveryState, runtime: Runtime[_RunData]) -> RecoveryState:
        data = runtime.context
        request = data.request
        diagnosis = state["diagnosis"].deterministic
        try:
            plan = self._planner.plan(request.failure, diagnosis, request.context, data.snapshot)
        except UnsafeRepair:
            if state["attempt_count"]:
                return _stop_retrying(RetryStopReason.NO_SAFE_ALTERNATIVE)
            return _finish(RecoveryStatus.PLAN_BLOCKED, "No safe proposal or trusted replacement could be established.")
        except Exception:
            return _finish(RecoveryStatus.PLAN_BLOCKED, "The repair planner could not safely produce a proposal.")

        replacement = plan.proposal.proposed_value
        if any(
            previous.target == plan.target
            and type(previous.proposal.proposed_value) is type(replacement)
            and previous.proposal.proposed_value == replacement
            for previous in data.attempted_plans
        ):
            return _stop_retrying(RetryStopReason.NO_SAFE_ALTERNATIVE)
        data.plan = plan
        return {
            "proposal": ProposalReference(
                plan.target.node_id, plan.target.field_name, plan.proposal.operation,
                plan.provenance.source_revision_id,
            ),
            "route": "reserve_attempt",
        }

    def _reserve_attempt(self, state: RecoveryState, runtime: Runtime[_RunData]) -> RecoveryState:
        if state["attempt_count"] >= MAX_AUTOMATIC_REPAIR_ATTEMPTS:
            return _stop_retrying(RetryStopReason.ATTEMPT_LIMIT_REACHED)
        runtime.context.attempted_plans.append(runtime.context.plan)
        number = state["attempt_count"] + 1
        return {
            "attempt_count": number,
            "attempts": (*state["attempts"], RecoveryAttempt(number, state["proposal"])),
            "candidate": None,
            "verification": None,
            "decision": VerificationStatus.NOT_RUN,
            "route": "apply_candidate",
        }

    def _apply_candidate(self, state: RecoveryState, runtime: Runtime[_RunData]) -> RecoveryState:
        data = runtime.context
        request = data.request
        try:
            candidate = self._planner.apply(
                data.plan, request.failure, state["diagnosis"].deterministic, request.context, data.snapshot,
            )
            snapshot = WorkflowSnapshot(
                state["original"].workflow_id, str(uuid4()), json.dumps(candidate.graph, allow_nan=False),
            )
        except Exception:
            reason = "Candidate application failed or its safety preconditions changed."
            return {
                **_update_attempt(state, status=AttemptStatus.APPLICATION_FAILED, explanation=reason),
                **_finish(RecoveryStatus.APPLICATION_FAILED, reason),
            }
        data.candidate = snapshot
        reference = _reference(snapshot)
        return {"candidate": reference, "route": "verify_candidate", **_update_attempt(state, candidate=reference)}

    def _verify_candidate(self, state: RecoveryState, runtime: Runtime[_RunData]) -> RecoveryState:
        data = runtime.context
        data.evidence = None
        if self._verifier is None:
            return {}
        original = state["original"]
        try:
            if data.baseline is None:
                baseline = self._verifier.get_baseline(original.workflow_id, original.revision_id, state["execution_run_id"])
                if not _baseline_matches(baseline, data.request):
                    return {}
                data.baseline = baseline
            data.evidence = self._verifier.verify(data.candidate, data.baseline)
        except Exception:
            return {}
        return {}

    def _evaluate_evidence(self, state: RecoveryState, runtime: Runtime[_RunData]) -> RecoveryState:
        data = runtime.context
        evidence = data.evidence
        candidate = state["candidate"]
        verification = None
        if isinstance(evidence, CandidateEvidence) and (
            evidence.candidate_workflow_id == candidate.workflow_id
            and evidence.baseline == data.baseline
        ):
            verification = _matched_verification(evidence.result, candidate.revision_id, data.baseline)
        decision = verification.status if verification is not None else VerificationStatus.NOT_RUN
        status, explanation = {
            VerificationStatus.PASSED: (AttemptStatus.VERIFIED, "All required checks passed on the candidate revision."),
            VerificationStatus.FAILED: (AttemptStatus.VERIFICATION_FAILED, "Verification reported a failed required check."),
            VerificationStatus.NOT_RUN: (
                AttemptStatus.VERIFICATION_UNAVAILABLE,
                "Candidate verification is unavailable, incomplete, or did not match the candidate and baseline.",
            ),
        }[decision]
        return {
            "decision": decision, "verification": verification,
            **_update_attempt(state, status=status, verification=verification, explanation=explanation),
        }

    def _decide(self, state: RecoveryState) -> RecoveryState:
        decision = state["decision"]
        if decision == VerificationStatus.PASSED:
            return {"route": "promote"}
        if decision == VerificationStatus.NOT_RUN:
            return _finish(RecoveryStatus.VERIFICATION_UNAVAILABLE, state["attempts"][-1].explanation)
        if state["attempt_count"] >= MAX_AUTOMATIC_REPAIR_ATTEMPTS:
            return _stop_retrying(RetryStopReason.ATTEMPT_LIMIT_REACHED)
        return {"route": "plan"}

    def _promote(self, state: RecoveryState, runtime: Runtime[_RunData]) -> RecoveryState:
        if self._lifecycle is None:
            return _finish(RecoveryStatus.VERIFIED_PENDING_PROMOTION, "The candidate is verified. Promotion is unavailable.")
        try:
            update = self._lifecycle.promote_candidate(
                runtime.context.candidate, expected_revision_id=state["original"].revision_id,
            )
        except Exception:
            update = RevisionUpdate.FAILED
        if update is RevisionUpdate.CONFIRMED:
            return {"promotion": RevisionUpdate.CONFIRMED, **_finish(
                RecoveryStatus.PROMOTED, "The adapter confirmed promotion of the verified candidate."
            )}
        if update is RevisionUpdate.CONFLICT:
            return {"promotion": RevisionUpdate.CONFLICT, **_finish(
                RecoveryStatus.REVISION_CONFLICT, "The active revision changed before promotion."
            )}
        return {"promotion": RevisionUpdate.FAILED, **_finish(
            RecoveryStatus.PROMOTION_FAILED, "Promotion of the verified candidate was not confirmed."
        )}

    def _rollback(self, state: RecoveryState) -> RecoveryState:
        if self._lifecycle is None:
            return _finish(RecoveryStatus.REPAIR_FAILED, "Repair failed. A rollback adapter is unavailable.")
        original = state["original"]
        try:
            previous = self._lifecycle.find_last_working_snapshot(original.workflow_id)
            if previous is None or _reference(previous) == original:
                return {"rollback": RollbackStatus.NO_WORKING_REVISION, **_finish(
                    RecoveryStatus.REPAIR_FAILED, "Repair failed and there is no separate working revision to restore."
                )}
            if previous.workflow_id != original.workflow_id:
                raise ValueError("Mismatched rollback workflow.")
            update = self._lifecycle.restore_snapshot(previous, expected_revision_id=original.revision_id)
        except Exception:
            update = RevisionUpdate.FAILED
        if update is RevisionUpdate.CONFIRMED:
            return {
                "rollback": RollbackStatus.RESTORED, "restored_revision": _reference(previous),
                **_finish(RecoveryStatus.ROLLED_BACK, "The adapter confirmed restoration of the last working revision."),
            }
        if update is RevisionUpdate.CONFLICT:
            return {"rollback": RollbackStatus.FAILED, **_finish(
                RecoveryStatus.REVISION_CONFLICT, "The active revision changed before rollback."
            )}
        return {"rollback": RollbackStatus.FAILED, **_finish(
            RecoveryStatus.ROLLBACK_FAILED, "Restoration of the last working revision was not confirmed."
        )}

    def _finalize(self, state: RecoveryState) -> RecoveryState:
        result = _result(state)
        if self._recorder is not None:
            try:
                for attempt in result.attempts:
                    self._recorder.record_attempt(result.original_revision, result.execution_run_id, attempt)
                self._recorder.record_outcome(result)
            except Exception:
                return {"result": replace(result, recorded=False)}
            result = replace(result, recorded=True)
        return {"result": result}


def _route(state: RecoveryState) -> str:
    return state["route"]


def _finish(status: RecoveryStatus, explanation: str) -> RecoveryState:
    return {"status": status, "explanation": explanation, "route": "finalize"}


def _stop_retrying(reason: RetryStopReason) -> RecoveryState:
    return {"route": "rollback", "retry_stop": reason}


def _reference(snapshot: WorkflowSnapshot) -> RevisionReference:
    return RevisionReference(snapshot.workflow_id, snapshot.revision_id)


def _update_attempt(state: RecoveryState, **changes) -> RecoveryState:
    attempts = state["attempts"]
    return {"attempts": (*attempts[:-1], replace(attempts[-1], **changes))}


def _baseline_matches(baseline: VerificationBaseline | None, request: RecoveryRequest) -> bool:
    if not isinstance(baseline, VerificationBaseline):
        return False
    failure = request.failure
    failed = {test.test_id for test in baseline.failed_tests}
    regression = {test.test_id for test in baseline.regression_tests}
    return (
        baseline.workflow_id == failure.workflow_id
        and baseline.workflow_revision_id == failure.workflow_revision_id
        and baseline.execution_run_id == failure.execution_run_id
        and failed == set(failure.failed_test_ids)
        and len(failed) == len(baseline.failed_tests) == len(failure.failed_test_ids)
        and len(regression) == len(baseline.regression_tests)
        and not failed.intersection(regression)
    )


def _matched_verification(
    result: VerificationResult, candidate_revision_id: str, baseline: VerificationBaseline
) -> VerificationResult | None:
    try:
        # Revalidate instances too, including anything constructed by an adapter.
        result = VerificationResult.model_validate(result.model_dump())
    except Exception:
        return None
    if (
        result.candidate_revision_id != candidate_revision_id
        or set(result.required_failed_test_ids) != {test.test_id for test in baseline.failed_tests}
        or set(result.required_regression_test_ids) != {test.test_id for test in baseline.regression_tests}
        or (result.execution is not None and result.execution.run_id == baseline.execution_run_id)
    ):
        return None
    tests_ran = bool(result.failed_test_reruns or result.regression_test_reruns)
    if result.structural_validation != VerificationStatus.PASSED:
        return result if result.execution is None and not tests_ran else None
    if result.execution is None or result.execution.status != VerificationStatus.PASSED:
        return result if not tests_ran else None
    return result


def _result(state: RecoveryState) -> RecoveryResult:
    return RecoveryResult(
        original_revision=state["original"], execution_run_id=state["execution_run_id"],
        status=state["status"], explanation=state["explanation"], diagnosis=state.get("diagnosis"),
        attempts=state["attempts"], promotion=state.get("promotion"),
        rollback=state.get("rollback", RollbackStatus.NOT_REQUIRED),
        restored_revision=state.get("restored_revision"), retry_stop=state.get("retry_stop"),
    )
