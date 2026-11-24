"""Dependency interfaces for a future repair coordinator.

Before wiring adapters, agree on durable revision and run IDs, stable test IDs,
and the canonical graph representation. The editor stores data.config.instructions
while the shared node catalog defines config.systemPrompt. Ports and condition
fields also differ. The existing maxRetries and AUTO_REPAIR_MAX_ATTEMPTS settings
need separate agreement from the two-attempt limit in the repair contract.

For diagnosis, Members 4 and 5 must agree on structured error codes and provide
field evidence tied to the failed node, run and revision. Member 3 must approve
the exact field names and policies for that revision's graph representation.
The adapter must confirm a permitted replacement source without passing its
value to the diagnoser. Unmapped graph formats and error codes need review.

The future LangGraph coordinator can call RepairPlanner.plan and apply after
diagnosis, retaining the original snapshot. The candidate must then pass
structural validation, execution, and the original failed and regression tests
before promotion. The coordinator should reserve and persist each attempt using
MAX_AUTOMATIC_REPAIR_ATTEMPTS from the repair contract. Planning and application
do not allocate attempts or provide durable enforcement across requests.
"""

from dataclasses import dataclass, field
from typing import Protocol

from app.schemas.repair import (
    CandidateExecution,
    FailureInformation,
    RepairProposal,
    RepairResult,
    TestVerification,
    VerificationStatus,
)
from app.services.repair.diagnosis import FailureDiagnoser, OriginalRequirements


@dataclass(frozen=True)
class WorkflowSnapshot:
    workflow_id: str
    revision_id: str
    graph_json: str = field(repr=False)


class RepairRepository(Protocol):
    """Member 1 owns storage and atomic revision checks."""

    def save_snapshot(self, workflow_id: str, revision_id: str) -> WorkflowSnapshot:
        """Persist and return an immutable copy of the requested revision."""
        ...

    def record_repair_result(self, execution_run_id: str, result: RepairResult) -> None: ...

    def find_last_working_snapshot(self, workflow_id: str) -> WorkflowSnapshot | None: ...

    def restore_snapshot(self, snapshot: WorkflowSnapshot, *, expected_revision_id: str) -> bool:
        """Restore only if the expected revision is still current."""
        ...


class RequirementsSource(Protocol):
    """Member 2 supplies original requirements and acceptance criteria."""

    def get_original_requirements(
        self, workflow_id: str, revision_id: str
    ) -> OriginalRequirements: ...


class WorkflowSchema(Protocol):
    """Member 3 owns how stored graphs map to supported nodes, fields and values."""

    def supports_proposal(self, snapshot: WorkflowSnapshot, proposal: RepairProposal) -> bool:
        """Check the target against supported settings and their allowed values."""
        ...


class WorkflowExecutor(Protocol):
    """Member 4 supplies run evidence and can execute an isolated candidate."""

    def get_failure(self, execution_run_id: str, revision_id: str) -> FailureInformation:
        """Return failure details with secrets and sensitive payloads removed."""
        ...

    def execute_candidate(self, candidate: WorkflowSnapshot) -> CandidateExecution: ...


class WorkflowVerifier(Protocol):
    """Member 5 owns validation and the original test definitions."""

    def validate_candidate(self, candidate: WorkflowSnapshot) -> VerificationStatus: ...

    def get_previously_passing_test_ids(
        self, workflow_id: str, revision_id: str
    ) -> tuple[str, ...]: ...

    def rerun_original_tests(
        self,
        candidate: WorkflowSnapshot,
        *,
        original_revision_id: str,
        test_ids: tuple[str, ...],
    ) -> tuple[TestVerification, ...]:
        """Run the existing inputs and assertions for the requested test IDs."""
        ...


@dataclass(frozen=True)
class RepairDependencies:
    repository: RepairRepository
    requirements: RequirementsSource
    workflow_schema: WorkflowSchema
    executor: WorkflowExecutor
    verifier: WorkflowVerifier
    diagnoser: FailureDiagnoser
