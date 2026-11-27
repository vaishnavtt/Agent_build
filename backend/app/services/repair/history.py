"""Allowlisted projection of durable recovery events. The host owns persistence."""
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Protocol

from fastapi import Request
from pydantic import AwareDatetime, Field

from app.schemas.repair import (
    MAX_AUTOMATIC_REPAIR_ATTEMPTS, FailureCategory, Identifier, RepairContract,
    RollbackStatus, VerificationResult, VerificationStatus,
)
from app.services.repair.diagnosis_router import DiagnosisStatus
from app.services.repair.recovery_contracts import (
    AttemptReport, AttemptStatus, RecoveryResult, RecoveryScope, RecoveryStatus, RevisionConflict, RevisionUpdate,
)


@dataclass(frozen=True)
class StoredRecovery:
    recovery_id: str
    result: RecoveryResult
    timestamp: datetime | None = None
    duration_ms: int | None = None


@dataclass(frozen=True)
class HistoryPage:
    scope: RecoveryScope
    records: tuple[StoredRecovery, ...]


class HistorySource(Protocol):
    def read(self, request: Request, scope: RecoveryScope, offset: int, limit: int) -> HistoryPage | None:
        """Reauthorize principal, resolve exact failed run, then read in stable newest-first order.
        None means unknown scope; empty records means a known failed execution with no recovery.
        Raise PermissionError for denial and RevisionConflict for stale references.
        """
        ...


class HistoryEntry(RepairContract):
    recovery_id: Identifier
    status: RecoveryStatus
    category: FailureCategory | None
    diagnosis_status: DiagnosisStatus | None
    attempts: tuple[AttemptReport, ...] = Field(max_length=MAX_AUTOMATIC_REPAIR_ATTEMPTS)
    promotion: RevisionUpdate | None
    rollback: RollbackStatus
    restored_revision_id: Identifier | None
    timestamp: AwareDatetime | None
    duration_ms: Annotated[int, Field(ge=0)] | None
    provider_duration_seconds: Annotated[float, Field(ge=0)] | None
    prompt_tokens: Annotated[int, Field(ge=0)] | None
    candidate_tokens: Annotated[int, Field(ge=0)] | None
    total_tokens: Annotated[int, Field(ge=0)] | None
    provider_calls: Annotated[int, Field(ge=0)] | None


class HistoryResponse(RepairContract):
    scope: RecoveryScope
    records: tuple[HistoryEntry, ...]
    next_offset: int | None


def project(record: StoredRecovery, scope: RecoveryScope) -> HistoryEntry:
    result = record.result
    original = result.original_revision
    if (original.workflow_id, original.revision_id, result.execution_run_id) != (
        scope.workflow_id, scope.workflow_revision_id, scope.execution_run_id
    ):
        raise ValueError("Mismatched recovery scope")
    attempts = []
    candidate_revisions = set()
    execution_runs = {scope.execution_run_id}
    for number, item in enumerate(result.attempts, 1):
        candidate, proof = item.candidate, item.verification
        if item.number != number or (candidate and (
            candidate.workflow_id != scope.workflow_id or candidate.revision_id == scope.workflow_revision_id
        )):
            raise ValueError("Invalid attempt reference")
        if candidate:
            if candidate.revision_id in candidate_revisions:
                raise ValueError("Duplicate candidate revision")
            candidate_revisions.add(candidate.revision_id)
        if proof is not None:
            proof = VerificationResult.model_validate(proof.model_dump())
        if proof and (not candidate or proof.candidate_revision_id != candidate.revision_id or
                      (proof.execution and proof.execution.run_id in execution_runs)):
            raise ValueError("Mismatched verification")
        if proof and proof.execution:
            execution_runs.add(proof.execution.run_id)
        status = proof.status if proof else VerificationStatus.NOT_RUN
        expected = {
            AttemptStatus.VERIFIED: VerificationStatus.PASSED,
            AttemptStatus.VERIFICATION_FAILED: VerificationStatus.FAILED,
        }.get(item.status, VerificationStatus.NOT_RUN)
        if status != expected:
            raise ValueError("Inconsistent attempt verification")
        attempts.append(AttemptReport(number=number, status=item.status, proposal=item.proposal,
                                      candidate=candidate, verification=proof, verification_status=status,
                                      explanation=item.status.value.replace("_", " ")))
    if result.status in (RecoveryStatus.PROMOTED, RecoveryStatus.VERIFIED_PENDING_PROMOTION):
        if not attempts or attempts[-1].status != AttemptStatus.VERIFIED:
            raise ValueError("Missing terminal verification")
    if (result.status == RecoveryStatus.PROMOTED) != (result.promotion == RevisionUpdate.CONFIRMED):
        raise ValueError("Inconsistent promotion")
    restored = result.restored_revision
    if (result.status == RecoveryStatus.ROLLED_BACK) != (result.rollback == RollbackStatus.RESTORED):
        raise ValueError("Inconsistent rollback")
    if result.rollback == RollbackStatus.RESTORED and not any(a.verification_status == VerificationStatus.FAILED for a in attempts):
        raise ValueError("Missing failed verification for rollback")
    if result.rollback == RollbackStatus.RESTORED and (
        not restored or restored.workflow_id != scope.workflow_id or restored.revision_id == scope.workflow_revision_id
    ):
        raise ValueError("Missing rollback reference")
    diagnosis = result.diagnosis
    return HistoryEntry(recovery_id=record.recovery_id, status=result.status,
                        category=diagnosis.diagnosis.category if diagnosis else None,
                        diagnosis_status=diagnosis.status if diagnosis else None, attempts=tuple(attempts),
                        promotion=result.promotion, rollback=result.rollback,
                        restored_revision_id=restored.revision_id if result.rollback == RollbackStatus.RESTORED else None,
                        timestamp=record.timestamp, duration_ms=record.duration_ms,
                        provider_duration_seconds=diagnosis.usage.duration_seconds if diagnosis else None,
                        prompt_tokens=diagnosis.usage.prompt_tokens if diagnosis else None,
                        candidate_tokens=diagnosis.usage.candidate_tokens if diagnosis else None,
                        total_tokens=diagnosis.usage.total_tokens if diagnosis else None,
                        provider_calls=diagnosis.usage.calls if diagnosis else None)
