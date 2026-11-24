"""Member 6 contracts for the in-memory recovery coordinator and its adapters."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from app.schemas.repair import (
    FailureInformation,
    Identifier,
    RepairContract,
    RepairOperation,
    RollbackStatus,
    VerificationResult,
)
from app.services.repair.diagnosis import DiagnosisContext, OriginalRequirements
from app.services.repair.diagnosis_router import DiagnosisOutcome
from app.services.repair.service import WorkflowSnapshot


class RecoveryStatus(StrEnum):
    ATTEMPT_RESERVATION_BLOCKED = "attempt_reservation_blocked"
    ATTEMPT_LIMIT_REACHED = "attempt_limit_reached"
    INVALID_CONTEXT = "invalid_context"
    HUMAN_REVIEW = "human_review"
    UNRESOLVED = "unresolved"
    SNAPSHOT_UNAVAILABLE = "snapshot_unavailable"
    PLAN_BLOCKED = "plan_blocked"
    APPLICATION_FAILED = "application_failed"
    VERIFICATION_UNAVAILABLE = "verification_unavailable"
    VERIFIED_PENDING_PROMOTION = "verified_pending_promotion"
    PROMOTED = "promoted"
    PROMOTION_FAILED = "promotion_failed"
    REVISION_CONFLICT = "revision_conflict"
    REPAIR_FAILED = "repair_failed"
    ROLLED_BACK = "rolled_back"
    ROLLBACK_FAILED = "rollback_failed"
    GRAPH_ERROR = "graph_error"


class AttemptStatus(StrEnum):
    STARTED = "started"
    APPLICATION_FAILED = "application_failed"
    VERIFICATION_UNAVAILABLE = "verification_unavailable"
    VERIFICATION_FAILED = "verification_failed"
    VERIFIED = "verified"
    INTERRUPTED = "interrupted"


class RetryStopReason(StrEnum):
    NO_SAFE_ALTERNATIVE = "no_safe_alternative"
    ATTEMPT_LIMIT_REACHED = "attempt_limit_reached"


class RevisionUpdate(StrEnum):
    CONFIRMED = "confirmed"
    CONFLICT = "conflict"
    FAILED = "failed"


class RevisionConflict(Exception):
    """A snapshot adapter found that the expected original revision is stale."""


class AttemptReservation(StrEnum):
    RESERVED = "reserved"
    LIMIT_REACHED = "limit_reached"
    CONFLICT = "conflict"
    UNAVAILABLE = "unavailable"


class RecoveryScope(RepairContract):
    workflow_id: Identifier
    workflow_revision_id: Identifier
    execution_run_id: Identifier


class DurableAttempts(Protocol):
    """Member 1 owns atomicity, uniqueness and persistence across workers."""

    def begin(self, scope: RecoveryScope) -> AttemptReservation:
        """Claim the recovery once for this scope, including completed requests."""
        ...

    def reserve(self, scope: RecoveryScope, number: int, *, limit: int) -> AttemptReservation:
        """Atomically reserve exactly this next attempt under the claimed scope."""
        ...

    def finish(self, scope: RecoveryScope, result: "RecoveryResult") -> None:
        """Record the terminal outcome without allowing the same scope to restart."""
        ...


def context_issue(failure: FailureInformation, context: DiagnosisContext | None) -> str | None:
    if context is None or (
        context.workflow_id != failure.workflow_id
        or context.workflow_revision_id != failure.workflow_revision_id
        or context.execution_run_id != failure.execution_run_id
    ):
        return "Trusted context does not match the failed run and revision."
    node_id = failure.failed_node_id
    if node_id is not None and sum(node.node_id == node_id for node in context.nodes) != 1:
        return "The failed node ID does not identify exactly one node."
    if context.configuration_evidence is not None and context.configuration_evidence.node_id != node_id:
        return "The field evidence conflicts with the failed node."
    return None


@dataclass(frozen=True)
class RecoveryRequest:
    failure: FailureInformation = field(repr=False)
    context: DiagnosisContext | None = field(repr=False)
    requirements: OriginalRequirements = field(repr=False)


@dataclass(frozen=True)
class RevisionReference:
    workflow_id: str
    revision_id: str


@dataclass(frozen=True)
class ProposalReference:
    node_id: str
    field_name: str
    operation: RepairOperation
    source_revision_id: str


class BaselineTest(RepairContract):
    test_id: Identifier
    definition_revision_id: Identifier


class VerificationBaseline(RepairContract):
    """References to the exact original inputs and assertions in Member 5's test store."""

    workflow_id: Identifier
    workflow_revision_id: Identifier
    execution_run_id: Identifier
    failed_tests: tuple[BaselineTest, ...]
    regression_tests: tuple[BaselineTest, ...]


@dataclass(frozen=True)
class CandidateEvidence:
    candidate_workflow_id: str
    baseline: VerificationBaseline
    result: VerificationResult


class RecoveryVerification(Protocol):
    def get_baseline(
        self, workflow_id: str, revision_id: str, execution_run_id: str
    ) -> VerificationBaseline | None: ...

    def verify(
        self, candidate: WorkflowSnapshot, baseline: VerificationBaseline
    ) -> CandidateEvidence | None:
        """Validate, execute and rerun the immutable tests on this isolated candidate.

        Bind every check to the supplied candidate and baseline. Candidate
        verification must not change the active workflow or original test suite.
        """
        ...


class SnapshotSource(Protocol):
    def save_snapshot(self, workflow_id: str, revision_id: str) -> WorkflowSnapshot | None: ...


class RevisionLifecycle(Protocol):
    """All active-revision changes must be atomic and check the expected revision."""

    def promote_candidate(self, candidate: WorkflowSnapshot, *, expected_revision_id: str) -> RevisionUpdate: ...

    def find_last_working_snapshot(self, workflow_id: str) -> WorkflowSnapshot | None: ...

    def restore_snapshot(self, snapshot: WorkflowSnapshot, *, expected_revision_id: str) -> RevisionUpdate: ...


@dataclass(frozen=True)
class RecoveryAttempt:
    number: int
    proposal: ProposalReference
    status: AttemptStatus = AttemptStatus.STARTED
    candidate: RevisionReference | None = None
    verification: VerificationResult | None = None
    explanation: str = ""


@dataclass(frozen=True)
class RecoveryResult:
    original_revision: RevisionReference
    execution_run_id: str
    status: RecoveryStatus
    explanation: str
    diagnosis: DiagnosisOutcome | None = None
    attempts: tuple[RecoveryAttempt, ...] = ()
    promotion: RevisionUpdate | None = None
    rollback: RollbackStatus = RollbackStatus.NOT_REQUIRED
    restored_revision: RevisionReference | None = None
    retry_stop: RetryStopReason | None = None
    recorded: bool | None = None


class RecoveryRecorder(Protocol):
    def record_attempt(
        self, original: RevisionReference, execution_run_id: str, attempt: RecoveryAttempt
    ) -> None: ...

    def record_outcome(self, result: RecoveryResult) -> None: ...
