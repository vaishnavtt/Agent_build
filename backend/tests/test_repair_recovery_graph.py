"""Compiled LangGraph tests with test-only execution and revision adapters."""

import json
from copy import deepcopy
from dataclasses import replace

import pytest

pytest.importorskip("langgraph.graph", reason="install requirements-langgraph.txt for recovery tests")

from langgraph.graph.state import CompiledStateGraph

from app.schemas.repair import CandidateExecution, RollbackStatus, VerificationResult, VerificationStatus
from app.schemas.repair import TestVerification as WorkflowTestVerification
from app.services.repair.diagnosis import (
    AcceptanceCriterion,
    DiagnosticCode,
    ExternalDiagnosisEvidence,
    ExternalDiagnosticFact,
    OriginalRequirements,
)
from app.services.repair.diagnosis_router import DiagnosisRouter, DiagnosisStatus
from app.services.repair.gemini_diagnosis import ComplexFailureCode, ProviderReply, ProviderUsage
from app.services.repair.recovery_contracts import (
    AttemptStatus,
    BaselineTest,
    CandidateEvidence,
    RecoveryRequest,
    RecoveryStatus,
    RetryStopReason,
    RevisionConflict,
    RevisionUpdate,
    VerificationBaseline,
)
from app.services.repair.recovery_graph import RecoveryGraph
from app.services.repair.service import WorkflowSnapshot
from tests.test_repair_planning import make_case


class FixtureGemini:
    def __init__(self):
        self.requests = []

    def generate(self, context):
        self.requests.append(context)
        return ProviderReply(text=json.dumps({
            "category": "execution",
            "suspected_cause": "output_contract_mismatch",
            "suggested_action": "review_output_contract",
            "evidence_refs": ["output_shape_mismatch"],
            "affected_node_ref": "affected_node",
            "affected_field": None,
            "human_investigation_recommended": True,
        }), usage=ProviderUsage(calls=1))


class FixtureRevisions:
    def __init__(self, snapshot):
        self.original = snapshot
        self.active = snapshot
        self.working = replace(snapshot, revision_id="working-revision")
        self.promote_result = RevisionUpdate.CONFIRMED
        self.restore_result = RevisionUpdate.CONFIRMED
        self.saved = []
        self.promotions = []
        self.restorations = []

    def save_snapshot(self, workflow_id, revision_id):
        self.saved.append((workflow_id, revision_id))
        if self.active.revision_id != revision_id:
            raise RevisionConflict("private newer revision detail")
        return self.original

    def promote_candidate(self, candidate, *, expected_revision_id):
        self.promotions.append((candidate, expected_revision_id))
        return self._set_current(candidate, expected_revision_id, self.promote_result)

    def find_last_working_snapshot(self, workflow_id):
        return self.working

    def restore_snapshot(self, snapshot, *, expected_revision_id):
        self.restorations.append((snapshot, expected_revision_id))
        return self._set_current(snapshot, expected_revision_id, self.restore_result)

    def _set_current(self, snapshot, expected_revision_id, result):
        if self.active.revision_id != expected_revision_id:
            return RevisionUpdate.CONFLICT
        if result == RevisionUpdate.CONFIRMED:
            self.active = snapshot
        return result


class FixtureVerifier:
    def __init__(self, failure):
        self.baseline = VerificationBaseline(
            workflow_id=failure.workflow_id,
            workflow_revision_id=failure.workflow_revision_id,
            execution_run_id=failure.execution_run_id,
            failed_tests=(BaselineTest(test_id="test-1", definition_revision_id="original-case-1"),),
            regression_tests=(BaselineTest(test_id="test-2", definition_revision_id="original-case-2"),),
        )
        self.baseline_requests = []
        self.candidates = []
        self.check = "passed"
        self.after_check = None

    def get_baseline(self, workflow_id, revision_id, execution_run_id):
        self.baseline_requests.append((workflow_id, revision_id, execution_run_id))
        return self.baseline

    def verify(self, candidate, baseline):
        self.candidates.append((candidate, baseline))
        run = CandidateExecution(run_id=f"candidate-run-{len(self.candidates)}", status="passed")
        failed = (WorkflowTestVerification(test_id="test-1", status="passed"),)
        regression = (WorkflowTestVerification(test_id="test-2", status="passed"),)
        data = {
            "candidate_revision_id": candidate.revision_id,
            "structural_validation": VerificationStatus.PASSED,
            "execution": run,
            "required_failed_test_ids": ("test-1",),
            "required_regression_test_ids": ("test-2",),
            "failed_test_reruns": failed,
            "regression_test_reruns": regression,
        }
        evidence_baseline = baseline
        workflow_id = candidate.workflow_id
        match self.check:
            case "structural":
                data.update(structural_validation="failed", execution=None, failed_test_reruns=(), regression_test_reruns=())
            case "execution":
                data.update(execution=run.model_copy(update={"status": VerificationStatus.FAILED}),
                            failed_test_reruns=(), regression_test_reruns=())
            case "failed_test":
                data["failed_test_reruns"] = (WorkflowTestVerification(test_id="test-1", status="failed"),)
            case "regression":
                data["regression_test_reruns"] = (WorkflowTestVerification(test_id="test-2", status="failed"),)
            case "missing_run":
                data.update(execution=None, failed_test_reruns=(), regression_test_reruns=())
            case "missing_test":
                data["regression_test_reruns"] = ()
            case "wrong_revision":
                data["candidate_revision_id"] = "different-candidate"
            case "wrong_workflow":
                workflow_id = "different-workflow"
            case "wrong_baseline":
                evidence_baseline = baseline.model_copy(update={"regression_tests": (
                    BaselineTest(test_id="test-2", definition_revision_id="changed-assertion"),
                )})
            case "wrong_test_ids":
                data.update(required_regression_test_ids=(), regression_test_reruns=())
            case "original_run":
                data["execution"] = CandidateExecution(run_id=baseline.execution_run_id, status="passed")
            case "contradictory":
                data["structural_validation"] = "failed"
            case "exception":
                raise RuntimeError("private verification data")
            case "none":
                return None
        evidence = CandidateEvidence(workflow_id, evidence_baseline, VerificationResult(**data))
        if self.after_check is not None:
            self.after_check(len(self.candidates))
        return evidence


class FixtureRecorder:
    def __init__(self):
        self.attempts = []
        self.outcomes = []

    def record_attempt(self, original, execution_run_id, attempt):
        self.attempts.append((original, execution_run_id, attempt))

    def record_outcome(self, result):
        self.outcomes.append(result)


@pytest.fixture
def rig():
    case = make_case()
    return (
        case,
        RecoveryRequest(case.failure, case.context, OriginalRequirements(
            "Summarize the document.", (AcceptanceCriterion("criterion-1", "Return valid JSON."),)
        )),
        FixtureGemini(),
        FixtureRevisions(case.snapshot),
        FixtureVerifier(case.failure),
    )


def make_graph(rig, *, verification=True, lifecycle=True, recorder=None, planner=None):
    case, _, gemini, revisions, verifier = rig
    return RecoveryGraph(
        DiagnosisRouter({"Output": (case.policy.definition,)}, gemini),
        planner if planner is not None else case.planner,
        revisions,
        verifier=verifier if verification else None,
        lifecycle=revisions if lifecycle else None,
        recorder=recorder,
    )


def test_compiled_graph_promotes_only_the_verified_isolated_candidate(rig):
    case, request, gemini, revisions, verifier = rig
    recorder = FixtureRecorder()
    graph = make_graph(rig, recorder=recorder)
    assert isinstance(graph.graph, CompiledStateGraph)
    assert {"diagnose", "reserve_attempt", "evaluate_evidence", "rollback"} <= set(graph.graph.get_graph().nodes)

    before = deepcopy(request)
    result = graph.recover(request)

    assert result.status == RecoveryStatus.PROMOTED
    assert result.promotion == RevisionUpdate.CONFIRMED
    assert result.rollback == RollbackStatus.NOT_REQUIRED
    assert result.diagnosis.status == DiagnosisStatus.DETERMINISTIC
    assert not gemini.requests
    attempt, = result.attempts
    assert attempt.number == 1
    assert attempt.proposal.field_name == "outputFormat"
    assert attempt.status == AttemptStatus.VERIFIED
    candidate, baseline = verifier.candidates[0]
    assert attempt.candidate.revision_id == attempt.verification.candidate_revision_id == candidate.revision_id
    assert attempt.verification.status == VerificationStatus.PASSED
    assert attempt.verification.failed_test_reruns[0].test_id == "test-1"
    assert attempt.verification.regression_test_reruns[0].test_id == "test-2"
    assert candidate.revision_id != case.snapshot.revision_id
    assert revisions.promotions == [(candidate, case.snapshot.revision_id)]
    assert revisions.active == candidate
    assert result.recorded
    assert len(recorder.attempts) == len(recorder.outcomes) == 1
    assert baseline.regression_tests[0].definition_revision_id == "original-case-2"

    assert request == before
    expected = json.loads(case.snapshot.graph_json)
    assert json.loads(revisions.original.graph_json) == expected
    assert expected["nodes"][1]["config"] == {}
    expected["nodes"][1]["config"]["outputFormat"] = "json"
    assert json.loads(candidate.graph_json) == expected


def test_gemini_fallback_is_advisory_and_stops_recovery(rig):
    _, request, gemini, revisions, verifier = rig
    request = replace(
        request,
        failure=request.failure.model_copy(update={"error_code": ComplexFailureCode.UNEXPECTED_OUTPUT_SHAPE}),
        context=replace(
            request.context, configuration_evidence=None,
            external_evidence=ExternalDiagnosisEvidence((ExternalDiagnosticFact.OUTPUT_SHAPE_MISMATCH,), True),
        ),
    )
    result = make_graph(rig).recover(request)

    assert result.status == RecoveryStatus.HUMAN_REVIEW
    assert result.diagnosis.status == DiagnosisStatus.ADVISORY
    assert result.diagnosis.usage.calls == len(gemini.requests) == 1
    assert result.attempts == ()
    assert revisions.saved == verifier.candidates == []


@pytest.mark.parametrize(
    ("code", "status"),
    [(DiagnosticCode.MISSING_REQUIRED_USER_INPUT, RecoveryStatus.HUMAN_REVIEW),
     ("UNLISTED_FAILURE", RecoveryStatus.UNRESOLVED)],
)
def test_non_repairable_failures_stop_before_snapshot(rig, code, status):
    _, request, gemini, revisions, _ = rig
    request = replace(request, failure=request.failure.model_copy(update={"error_code": code}))
    result = make_graph(rig).recover(request)
    assert result.status == status
    assert result.attempts == ()
    assert revisions.saved == gemini.requests == []


@pytest.mark.parametrize("case", ["missing", "revision", "run", "duplicate", "field_node"])
def test_invalid_or_contradictory_context_is_rejected(rig, case):
    _, request, gemini, revisions, _ = rig
    context = request.context
    contexts = {
        "missing": None,
        "revision": replace(context, workflow_revision_id="other"),
        "run": replace(context, execution_run_id="other"),
        "duplicate": replace(context, nodes=context.nodes * 2),
        "field_node": replace(context, configuration_evidence=replace(context.configuration_evidence, node_id="other")),
    }
    result = make_graph(rig).recover(replace(request, context=contexts[case]))
    assert result.status == RecoveryStatus.INVALID_CONTEXT
    assert result.diagnosis is None
    assert result.attempts == ()
    assert revisions.saved == gemini.requests == []


def test_missing_verifier_never_marks_candidate_verified(rig):
    case, request, _, revisions, _ = rig
    result = make_graph(rig, verification=False).recover(request)
    assert result.status == RecoveryStatus.VERIFICATION_UNAVAILABLE
    attempt, = result.attempts
    assert attempt.status == AttemptStatus.VERIFICATION_UNAVAILABLE
    assert attempt.candidate is not None
    assert attempt.verification is None
    assert revisions.active == case.snapshot
    assert revisions.promotions == revisions.restorations == []


def test_graph_state_only_exposes_references_and_safe_summaries(rig, monkeypatch):
    case, request, _, revisions, _ = rig
    snapshot = json.loads(case.snapshot.graph_json)
    snapshot["nodes"][0]["config"]["apiKey"] = "synthetic-unrelated-secret"
    revisions.original = replace(case.snapshot, graph_json=json.dumps(snapshot))
    graph = make_graph(rig)
    stream = graph.graph.stream
    states = []

    def collecting_stream(*args, **kwargs):
        for state in stream(*args, **kwargs):
            states.append(state)
            yield state

    monkeypatch.setattr(graph.graph, "stream", collecting_stream)
    request = replace(request, failure=request.failure.model_copy(update={
        "error_message": "synthetic-private-diagnostic",
        "safe_diagnostic_evidence": ("synthetic-private-log",),
    }))
    assert graph.recover(request).status == RecoveryStatus.PROMOTED
    assert any(state.get("candidate") is not None for state in states)
    assert "synthetic-unrelated-secret" in revisions.active.graph_json
    for sensitive in ("synthetic-unrelated-secret", "synthetic-private-diagnostic", "synthetic-private-log"):
        assert sensitive not in repr(states)


@pytest.mark.parametrize("check", ["structural", "execution", "failed_test", "regression"])
def test_failed_checks_consume_attempt_and_never_promote(rig, check):
    case, request, _, revisions, verifier = rig
    verifier.check = check
    result = make_graph(rig, lifecycle=False).recover(request)

    assert result.status == RecoveryStatus.REPAIR_FAILED
    attempt, = result.attempts
    assert attempt.number == 1
    assert attempt.status == AttemptStatus.VERIFICATION_FAILED
    assert attempt.verification.status == VerificationStatus.FAILED
    assert revisions.active == case.snapshot
    assert not revisions.promotions


@pytest.mark.parametrize(
    "check",
    ["missing_run", "missing_test", "wrong_revision", "wrong_workflow", "wrong_baseline",
     "wrong_test_ids", "original_run", "contradictory", "exception", "none"],
)
def test_bad_verification_evidence_leaves_original_active(rig, check):
    case, request, _, revisions, verifier = rig
    verifier.check = check
    result = make_graph(rig).recover(request)

    assert result.status == RecoveryStatus.VERIFICATION_UNAVAILABLE
    assert result.attempts[0].status == AttemptStatus.VERIFICATION_UNAVAILABLE
    assert revisions.active == case.snapshot
    assert revisions.promotions == revisions.restorations == []
    assert "private verification data" not in repr(result)


def test_missing_or_wrong_baseline_prevents_verifier_execution(rig):
    _, request, _, revisions, verifier = rig
    baseline = verifier.baseline
    graph = make_graph(rig)
    for value in (None, baseline.model_copy(update={"failed_tests": ()})):
        verifier.baseline = value
        assert graph.recover(request).status == RecoveryStatus.VERIFICATION_UNAVAILABLE
    assert verifier.candidates == revisions.promotions == []


def test_first_failure_then_different_trusted_replacement_can_promote(rig):
    case, request, _, revisions, verifier = rig
    verifier.check = "failed_test"

    def enable_second_candidate(number):
        if number == 1:
            case.provider.value = "markdown"
            case.provider.source_revision_id = "another-working-revision"
            verifier.check = "passed"

    verifier.after_check = enable_second_candidate
    result = make_graph(rig).recover(request)

    assert result.status == RecoveryStatus.PROMOTED
    assert [item.status for item in result.attempts] == [AttemptStatus.VERIFICATION_FAILED, AttemptStatus.VERIFIED]
    assert [item.number for item in result.attempts] == [1, 2]
    assert len(revisions.saved) == len(verifier.baseline_requests) == 1
    assert verifier.candidates[0][1] is verifier.candidates[1][1]
    assert revisions.active == verifier.candidates[1][0]
    assert result.attempts[0].candidate != result.attempts[1].candidate
    assert json.loads(revisions.active.graph_json)["nodes"][1]["config"]["outputFormat"] == "markdown"


def test_changed_provenance_alone_does_not_repeat_rejected_value(rig):
    case, request, _, revisions, verifier = rig
    verifier.check = "regression"

    def change_source(_):
        case.provider.source_revision_id = "other-trusted-source"

    verifier.after_check = change_source
    result = make_graph(rig).recover(request)

    assert result.status == RecoveryStatus.ROLLED_BACK
    assert result.rollback == RollbackStatus.RESTORED
    assert result.retry_stop == RetryStopReason.NO_SAFE_ALTERNATIVE
    assert len(result.attempts) == len(verifier.candidates) == 1
    assert revisions.restorations == [(revisions.working, case.snapshot.revision_id)]
    assert revisions.active == revisions.working


def test_two_attempts_is_the_maximum_even_if_another_value_becomes_available(rig):
    case, request, _, revisions, verifier = rig
    verifier.check = "structural"

    def next_value(number):
        case.provider.value = "markdown" if number == 1 else "json"

    verifier.after_check = next_value
    result = make_graph(rig).recover(request)
    assert result.status == RecoveryStatus.ROLLED_BACK
    assert result.retry_stop == RetryStopReason.ATTEMPT_LIMIT_REACHED
    assert [item.number for item in result.attempts] == [1, 2]
    assert len(verifier.candidates) == 2
    assert not revisions.promotions


def test_missing_trusted_replacement_and_unsafe_application_stop_safely(rig, monkeypatch):
    case, request, _, revisions, _ = rig
    case.provider.available = False
    result = make_graph(rig).recover(request)
    assert result.status == RecoveryStatus.PLAN_BLOCKED
    assert result.attempts == ()

    case.provider.available = True
    planner = case.planner

    def fail(*args):
        raise RuntimeError("private candidate information")

    monkeypatch.setattr(planner, "apply", fail)
    result = make_graph(rig, planner=planner).recover(request)
    assert result.status == RecoveryStatus.APPLICATION_FAILED
    attempt, = result.attempts
    assert attempt.number == 1
    assert attempt.status == AttemptStatus.APPLICATION_FAILED
    assert revisions.active == case.snapshot
    assert "private candidate information" not in repr(result)


def test_verified_candidate_without_promotion_adapter_is_pending(rig):
    case, request, _, revisions, _ = rig
    result = make_graph(rig, lifecycle=False).recover(request)
    assert result.status == RecoveryStatus.VERIFIED_PENDING_PROMOTION
    assert result.attempts[0].status == AttemptStatus.VERIFIED
    assert result.promotion is None
    assert revisions.active == case.snapshot


def test_unconfirmed_promotion_is_not_reported_as_active(rig):
    case, request, _, revisions, _ = rig
    revisions.promote_result = RevisionUpdate.FAILED
    result = make_graph(rig).recover(request)
    assert result.status == RecoveryStatus.PROMOTION_FAILED
    assert result.promotion == RevisionUpdate.FAILED
    assert result.attempts[0].status == AttemptStatus.VERIFIED
    assert revisions.active == case.snapshot
    assert not revisions.restorations


@pytest.mark.parametrize("check", ["passed", "regression"])
def test_revision_conflict_leaves_newer_active_revision_in_place(rig, check):
    case, request, _, revisions, verifier = rig
    verifier.check = check
    newer = replace(case.snapshot, revision_id="newer-user-edit")
    verifier.after_check = lambda _: setattr(revisions, "active", newer)
    result = make_graph(rig).recover(request)
    assert result.status == RecoveryStatus.REVISION_CONFLICT
    assert revisions.active == newer
    assert result.restored_revision is None
    assert result.promotion != RevisionUpdate.CONFIRMED


def test_stale_revision_rejected_while_obtaining_snapshot(rig):
    case, request, _, revisions, verifier = rig
    revisions.active = replace(case.snapshot, revision_id="newer")
    result = make_graph(rig).recover(request)
    assert result.status == RecoveryStatus.REVISION_CONFLICT
    assert result.attempts == ()
    assert verifier.candidates == []


@pytest.mark.parametrize("working_exists", [True, False])
def test_rollback_failure_and_no_working_revision_preserve_original(rig, working_exists):
    case, request, _, revisions, verifier = rig
    verifier.check = "failed_test"
    revisions.restore_result = RevisionUpdate.FAILED
    if not working_exists:
        revisions.working = None
    result = make_graph(rig).recover(request)
    assert result.status == (RecoveryStatus.ROLLBACK_FAILED if working_exists else RecoveryStatus.REPAIR_FAILED)
    assert result.rollback == (RollbackStatus.FAILED if working_exists else RollbackStatus.NO_WORKING_REVISION)
    assert result.restored_revision is None
    assert revisions.active == case.snapshot


@pytest.mark.parametrize("stage", ["snapshot", "promote", "rollback", "record"])
def test_adapter_exceptions_are_reported_without_raw_error_data(rig, monkeypatch, stage):
    _, request, _, revisions, verifier = rig
    recorder = FixtureRecorder()

    def fail(*args, **kwargs):
        raise RuntimeError("private adapter details")

    if stage == "rollback":
        verifier.check = "regression"
    mapping = {
        "snapshot": (revisions, "save_snapshot", RecoveryStatus.SNAPSHOT_UNAVAILABLE),
        "promote": (revisions, "promote_candidate", RecoveryStatus.PROMOTION_FAILED),
        "rollback": (revisions, "restore_snapshot", RecoveryStatus.ROLLBACK_FAILED),
        "record": (recorder, "record_outcome", RecoveryStatus.PROMOTED),
    }
    adapter, method, expected = mapping[stage]
    monkeypatch.setattr(adapter, method, fail)
    result = make_graph(rig, recorder=recorder).recover(request)
    assert result.status == expected
    assert "private adapter details" not in repr(result)
    assert result.recorded is (stage != "record")


def test_unexpected_graph_failure_is_terminal_and_preserves_attempt(rig, monkeypatch):
    _, request, _, revisions, _ = rig
    from app.services.repair import recovery_graph

    def fail(*args):
        raise RuntimeError("private graph details")

    monkeypatch.setattr(recovery_graph, "_matched_verification", fail)
    result = make_graph(rig).recover(request)
    assert result.status == RecoveryStatus.GRAPH_ERROR
    assert result.attempts[0].number == 1
    assert result.attempts[0].status == AttemptStatus.INTERRUPTED
    assert revisions.promotions == revisions.restorations == []
    assert "private graph details" not in repr(result)
