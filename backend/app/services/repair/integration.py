"""Server-side repair wiring. Team adapters are installed by the host application."""

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from importlib.util import find_spec
from typing import Literal, Protocol

from fastapi import Request
from pydantic import Field

from app.schemas.repair import (
    MAX_AUTOMATIC_REPAIR_ATTEMPTS,
    DiagnosisResult,
    FailureInformation,
    RepairContract,
    RollbackStatus,
    VerificationResult,
    VerificationStatus,
)
from app.services.repair.diagnosis import DiagnosisContext, OriginalRequirements
from app.services.repair.diagnosis_router import DiagnosisOutcome, DiagnosisRouter, DiagnosisStatus
from app.services.repair.gemini_diagnosis import GeminiDiagnosisProvider, GeminiProvider, ProviderIssue
from app.services.repair.planning import RepairPlanner, ReplacementProvider, ScalarFieldPolicy
from app.services.repair.recovery_contracts import (
    AttemptReservation,
    AttemptStatus,
    DurableAttempts,
    ProposalReference,
    RecoveryRecorder,
    RecoveryRequest,
    RecoveryResult,
    RecoveryScope,
    RecoveryStatus,
    RecoveryVerification,
    RetryStopReason,
    RevisionConflict,
    RevisionLifecycle,
    RevisionReference,
    RevisionUpdate,
    SnapshotSource,
    context_issue,
)
from app.services.repair.service import RequirementsSource

RepairAction = Literal["diagnose", "recover"]


class RepairAccess(Protocol):
    def allows(self, request: Request, scope: RecoveryScope, action: RepairAction) -> bool:
        """Authorize the scoped operation via the host's authenticated identity."""
        ...


class FailureSource(Protocol):
    def get_failure(self, scope: RecoveryScope) -> tuple[FailureInformation, DiagnosisContext] | None:
        """Load redacted evidence and approved diagnostic context for the requested run."""
        ...


class Availability(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    INCOMPATIBLE = "incompatible"
    NOT_CONFIGURED = "not_configured"
    HUMAN_INTERVENTION = "requires_human_intervention"


class Dependency(StrEnum):
    AUTHORIZATION = "authorization"
    FAILURE_EVIDENCE = "failure_evidence"
    SNAPSHOT = "snapshot"
    SCHEMA_POLICY = "schema_policy"
    REPLACEMENT = "replacement"
    ORIGINAL_REQUIREMENTS = "original_requirements"
    ATTEMPT_RESERVATION = "attempt_reservation"
    CANDIDATE_EXECUTION = "candidate_execution"
    STRUCTURAL_VALIDATION = "structural_validation"
    REGRESSION_VERIFICATION = "regression_verification"
    REVISION_LIFECYCLE = "revision_lifecycle"
    REPAIR_RECORDING = "repair_recording"
    RECOVERY_RUNTIME = "recovery_runtime"


@dataclass(frozen=True)
class RepairBindings:
    access: RepairAccess | None = None
    failures: FailureSource | None = None
    requirements: RequirementsSource | None = None
    policies: Mapping[str, tuple[ScalarFieldPolicy, ...]] = field(default_factory=dict)
    replacements: ReplacementProvider | None = None
    snapshots: SnapshotSource | None = None
    attempts: DurableAttempts | None = None
    verifier: RecoveryVerification | None = None
    lifecycle: RevisionLifecycle | None = None
    recorder: RecoveryRecorder | None = None
    gemini: GeminiProvider | None = None
    availability: Mapping[Dependency, Availability] = field(default_factory=dict)


class RepairReadiness(RepairContract):
    diagnosis_available: bool
    recovery_available: bool
    max_attempts: int = MAX_AUTOMATIC_REPAIR_ATTEMPTS
    dependencies: dict[Dependency, Availability]
    blockers: tuple[Dependency, ...]


class RequestStatus(StrEnum):
    DEPENDENCIES_UNAVAILABLE = "dependencies_unavailable"
    FORBIDDEN = "forbidden"
    FAILURE_NOT_FOUND = "failure_not_found"
    DUPLICATE_REQUEST = "duplicate_request"


class AttemptReport(RepairContract):
    number: int
    status: AttemptStatus
    proposal: ProposalReference
    candidate: RevisionReference | None = None
    verification: VerificationResult | None = None
    verification_status: VerificationStatus
    explanation: str


class RepairResponse(RepairContract):
    status: RecoveryStatus | DiagnosisStatus | RequestStatus
    explanation: str
    readiness: RepairReadiness | None = None
    diagnosis: DiagnosisResult | None = None
    diagnosis_status: DiagnosisStatus | None = None
    provider_issue: ProviderIssue | None = None
    attempts: tuple[AttemptReport, ...] = Field(default=(), max_length=MAX_AUTOMATIC_REPAIR_ATTEMPTS)
    promotion: RevisionUpdate | None = None
    rollback: RollbackStatus = RollbackStatus.NOT_REQUIRED
    restored_revision: RevisionReference | None = None
    retry_stop: RetryStopReason | None = None
    recorded: bool | None = None


class RepairService:
    def __init__(self, bindings: RepairBindings) -> None:
        self._bindings = bindings

    def readiness(self) -> RepairReadiness:
        b = self._bindings
        adapters = {
            Dependency.AUTHORIZATION: b.access,
            Dependency.FAILURE_EVIDENCE: b.failures,
            Dependency.SNAPSHOT: b.snapshots,
            Dependency.SCHEMA_POLICY: any(b.policies.values()),
            Dependency.REPLACEMENT: b.replacements,
            Dependency.ORIGINAL_REQUIREMENTS: b.requirements,
            Dependency.ATTEMPT_RESERVATION: b.attempts,
            Dependency.CANDIDATE_EXECUTION: b.verifier,
            Dependency.STRUCTURAL_VALIDATION: b.verifier,
            Dependency.REGRESSION_VERIFICATION: b.verifier,
            Dependency.REVISION_LIFECYCLE: b.lifecycle,
            Dependency.REPAIR_RECORDING: b.recorder,
            Dependency.RECOVERY_RUNTIME: find_spec("langgraph") is not None,
        }
        statuses = {
            key: b.availability.get(key, Availability.AVAILABLE) if adapter
            else Availability.NOT_CONFIGURED
            for key, adapter in adapters.items()
        }
        blockers = tuple(key for key, value in statuses.items() if value is not Availability.AVAILABLE)
        return RepairReadiness(
            diagnosis_available=all(key not in blockers for key in (Dependency.AUTHORIZATION, Dependency.FAILURE_EVIDENCE)),
            recovery_available=not blockers,
            dependencies=statuses, blockers=blockers,
        )

    def run(self, scope: RecoveryScope, request: Request, action: RepairAction) -> tuple[int, RepairResponse]:
        b = self._bindings
        readiness = self.readiness()
        if not readiness.diagnosis_available or b.access is None or b.failures is None:
            return _blocked_for_action(readiness, action)
        try:
            allowed = b.access.allows(request, scope, action)
        except Exception:
            return _blocked(readiness, "Repair authorization could not be checked.")
        if allowed is not True:
            return 403, RepairResponse(status=RequestStatus.FORBIDDEN, explanation="Access to the repair request was denied.")
        if action == "recover" and not readiness.recovery_available:
            return _blocked_for_action(readiness, action)

        try:
            found = b.failures.get_failure(scope)
            if found is None:
                return 404, RepairResponse(status=RequestStatus.FAILURE_NOT_FOUND, explanation="No trusted failure was found for this run.")
            failure, context = found
            if (failure.workflow_id, failure.workflow_revision_id, failure.execution_run_id) != (
                scope.workflow_id, scope.workflow_revision_id, scope.execution_run_id
            ):
                return 409, RepairResponse(status=RecoveryStatus.INVALID_CONTEXT, explanation="Failure identity does not match the request.")
            if issue := context_issue(failure, context):
                return 409, RepairResponse(status=RecoveryStatus.INVALID_CONTEXT, explanation=issue)
            requirements = None
            if b.requirements is not None and readiness.dependencies[Dependency.ORIGINAL_REQUIREMENTS] is Availability.AVAILABLE:
                requirements = b.requirements.get_original_requirements(scope.workflow_id, scope.workflow_revision_id)
        except RevisionConflict:
            return 409, RepairResponse(status=RecoveryStatus.REVISION_CONFLICT, explanation="The requested revision is no longer current.")
        except Exception:
            return _blocked(readiness, "Trusted repair inputs could not be retrieved.")

        policies = b.policies if readiness.dependencies[Dependency.SCHEMA_POLICY] is Availability.AVAILABLE else {}
        router = DiagnosisRouter(
            {node_type: tuple(policy.definition for policy in fields) for node_type, fields in policies.items()},
            b.gemini if b.gemini is not None else GeminiDiagnosisProvider.from_backend_settings(),
        )
        if action == "diagnose":
            outcome = router.diagnose_with_details(
                failure, requirements or OriginalRequirements("", ()), context=context,
            )
            return 200, RepairResponse(status=outcome.status, explanation=outcome.diagnosis.root_cause, **_diagnosis(outcome))
        if requirements is None:
            return _blocked(readiness, "Original requirements for the requested revision are unavailable.")
        return self._recover(scope, RecoveryRequest(failure, context, requirements), router, readiness)

    def _recover(
        self, scope: RecoveryScope, request: RecoveryRequest, router: DiagnosisRouter, readiness: RepairReadiness,
    ) -> tuple[int, RepairResponse]:
        b = self._bindings
        attempts = b.attempts
        if attempts is None or b.snapshots is None or b.replacements is None:
            return _blocked_for_action(readiness, "recover")
        try:
            from app.services.repair.recovery_graph import RecoveryGraph

            graph = RecoveryGraph(
                router, RepairPlanner(b.policies, b.replacements), b.snapshots,
                verifier=b.verifier, lifecycle=b.lifecycle, recorder=b.recorder,
            )
            claim = attempts.begin(scope)
        except RevisionConflict:
            return 409, RepairResponse(status=RecoveryStatus.REVISION_CONFLICT, explanation="The requested revision is no longer current.")
        except Exception:
            return _blocked(readiness, "The recovery runtime or durable request claim is unavailable.")
        if claim is AttemptReservation.CONFLICT:
            return 409, RepairResponse(status=RequestStatus.DUPLICATE_REQUEST, explanation="Recovery was already claimed for this run and revision.")
        if claim is AttemptReservation.LIMIT_REACHED:
            return 409, RepairResponse(status=RecoveryStatus.ATTEMPT_LIMIT_REACHED, explanation="The durable repair budget is exhausted.")
        if claim is not AttemptReservation.RESERVED:
            return _blocked(readiness, "A durable request claim could not be confirmed.")

        result = graph.recover(request, reserve=lambda number: attempts.reserve(scope, number, limit=MAX_AUTOMATIC_REPAIR_ATTEMPTS))
        try:
            attempts.finish(scope, result)
        except Exception:
            result = replace(result, recorded=False, explanation=result.explanation + " Durable outcome recording could not be confirmed.")
        return _result_response(result)


def _blocked(readiness: RepairReadiness, message: str = "Required production repair adapters are unavailable.") -> tuple[int, RepairResponse]:
    return 503, RepairResponse(status=RequestStatus.DEPENDENCIES_UNAVAILABLE, explanation=message, readiness=readiness)


def _blocked_for_action(readiness: RepairReadiness, action: RepairAction) -> tuple[int, RepairResponse]:
    if action == "recover" and Dependency.ATTEMPT_RESERVATION in readiness.blockers:
        return _blocked(readiness, "Automatic recovery across requests requires durable attempt reservation.")
    return _blocked(readiness)


def _diagnosis(outcome: DiagnosisOutcome | None) -> dict:
    if outcome is None:
        return {}
    return {"diagnosis": outcome.diagnosis, "diagnosis_status": outcome.status, "provider_issue": outcome.provider_issue}


def _result_response(result: RecoveryResult) -> tuple[int, RepairResponse]:
    status_code = {
        RecoveryStatus.INVALID_CONTEXT: 409,
        RecoveryStatus.REVISION_CONFLICT: 409,
        RecoveryStatus.ATTEMPT_LIMIT_REACHED: 409,
        RecoveryStatus.ATTEMPT_RESERVATION_BLOCKED: 503,
        RecoveryStatus.SNAPSHOT_UNAVAILABLE: 503,
        RecoveryStatus.VERIFICATION_UNAVAILABLE: 503,
        RecoveryStatus.GRAPH_ERROR: 500,
    }.get(result.status, 200)
    return status_code, RepairResponse(
        status=result.status, explanation=result.explanation, **_diagnosis(result.diagnosis),
        attempts=tuple(AttemptReport(
            number=item.number, status=item.status, proposal=item.proposal, candidate=item.candidate,
            verification=item.verification, explanation=item.explanation,
            verification_status=item.verification.status if item.verification else VerificationStatus.NOT_RUN,
        ) for item in result.attempts),
        promotion=result.promotion, rollback=result.rollback, restored_revision=result.restored_revision,
        retry_stop=result.retry_stop, recorded=result.recorded,
    )
