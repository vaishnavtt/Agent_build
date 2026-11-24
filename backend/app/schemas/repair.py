"""Provisional Member 6 contracts for diagnosis and verified workflow repair."""

from enum import StrEnum
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    StringConstraints,
    model_validator,
)

MAX_AUTOMATIC_REPAIR_ATTEMPTS = 2

Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]
DiagnosticText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
ConfigurationField = Annotated[str, StringConstraints(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$", max_length=128)]
ConfigurationValue = StrictStr | StrictBool | StrictInt | StrictFloat | None


class RepairContract(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, hide_input_in_errors=True, allow_inf_nan=False
    )


class FailureCategory(StrEnum):
    CONFIGURATION = "configuration"
    CONNECTION = "connection"
    DATA_MAPPING = "data_mapping"
    MISSING_INPUT = "missing_input"
    CREDENTIALS = "credentials"
    EXECUTION = "execution"
    TEST_ASSERTION = "test_assertion"
    UNKNOWN = "unknown"


class RepairOperation(StrEnum):
    SET_CONFIGURATION_FIELD = "set_configuration_field"


class VerificationStatus(StrEnum):
    NOT_RUN = "not_run"
    PASSED = "passed"
    FAILED = "failed"


class RepairStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    HUMAN_INTERVENTION_REQUIRED = "human_intervention_required"
    NOT_REPAIRABLE = "not_repairable"


class RollbackStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    RESTORED = "restored"
    NO_WORKING_REVISION = "no_working_revision"
    FAILED = "failed"


class FailureInformation(RepairContract):
    """Failure tied to a workflow revision. The caller supplies redacted text."""

    workflow_id: Identifier
    workflow_revision_id: Identifier
    execution_run_id: Identifier
    failed_node_id: Identifier | None = None
    error_code: Identifier
    error_message: DiagnosticText = Field(repr=False)
    safe_diagnostic_evidence: tuple[DiagnosticText, ...] = Field(default=(), repr=False)
    failed_test_ids: tuple[Identifier, ...] = ()


class DiagnosisResult(RepairContract):
    category: FailureCategory
    affected_node_id: Identifier | None = None
    affected_configuration_field: ConfigurationField | None = None
    root_cause: DiagnosticText = Field(repr=False)
    supporting_evidence: tuple[DiagnosticText, ...] = Field(default=(), repr=False)
    repairable: bool
    requires_human_intervention: bool


class RepairProposal(RepairContract):
    """One scalar setting on one node. The snapshot supplies the actual prior state."""

    target_node_id: Identifier
    operation: RepairOperation
    target_configuration_field: ConfigurationField
    original_value: ConfigurationValue = Field(repr=False)
    proposed_value: ConfigurationValue = Field(repr=False)
    reason: DiagnosticText = Field(repr=False)


class CandidateExecution(RepairContract):
    run_id: Identifier
    status: VerificationStatus


class TestVerification(RepairContract):
    test_id: Identifier
    status: VerificationStatus


class VerificationResult(RepairContract):
    """Evidence for the final attempt, supplied by execution and testing adapters."""

    candidate_revision_id: Identifier
    structural_validation: VerificationStatus
    required_failed_test_ids: tuple[Identifier, ...]
    required_regression_test_ids: tuple[Identifier, ...]
    execution: CandidateExecution | None = None
    failed_test_reruns: tuple[TestVerification, ...] = ()
    regression_test_reruns: tuple[TestVerification, ...] = ()

    @model_validator(mode="after")
    def check_test_evidence(self) -> Self:
        expected = self.required_failed_test_ids + self.required_regression_test_ids
        if len(expected) != len(set(expected)):
            raise ValueError("required test IDs must be unique across both groups")
        for required, reruns in (
            (self.required_failed_test_ids, self.failed_test_reruns),
            (self.required_regression_test_ids, self.regression_test_reruns),
        ):
            observed = {test.test_id for test in reruns}
            if len(observed) != len(reruns) or not observed.issubset(required):
                raise ValueError("rerun results must refer to unique IDs in their required group")
        return self

    @property
    def status(self) -> VerificationStatus:
        checks = [self.structural_validation]
        checks.append(self.execution.status if self.execution else VerificationStatus.NOT_RUN)
        checks.extend(test.status for test in self.failed_test_reruns + self.regression_test_reruns)
        if VerificationStatus.FAILED in checks:
            return VerificationStatus.FAILED
        if VerificationStatus.NOT_RUN in checks:
            return VerificationStatus.NOT_RUN
        if len(self.failed_test_reruns) != len(self.required_failed_test_ids):
            return VerificationStatus.NOT_RUN
        if len(self.regression_test_reruns) != len(self.required_regression_test_ids):
            return VerificationStatus.NOT_RUN
        return VerificationStatus.PASSED


class RepairAttempt(RepairContract):
    attempt_number: Annotated[int, Field(strict=True, ge=1, le=MAX_AUTOMATIC_REPAIR_ATTEMPTS)]
    diagnosis: DiagnosisResult
    proposed_changes: tuple[RepairProposal, ...] = ()
    verification_status: VerificationStatus = VerificationStatus.NOT_RUN
    failure_reason: DiagnosticText | None = Field(default=None, repr=False)

    @model_validator(mode="after")
    def check_attempt(self) -> Self:
        if self.verification_status == VerificationStatus.PASSED:
            if not self.proposed_changes or self.failure_reason:
                raise ValueError("a passed attempt requires proposed changes and no failure reason")
        if self.verification_status == VerificationStatus.FAILED and not self.failure_reason:
            raise ValueError("a failed verification requires a failure reason")
        if self.proposed_changes:
            if not self.diagnosis.repairable or self.diagnosis.requires_human_intervention:
                raise ValueError("automatic changes require a repairable diagnosis without human intervention")
            if self.diagnosis.category in (FailureCategory.CREDENTIALS, FailureCategory.MISSING_INPUT):
                raise ValueError("automatic changes cannot supply credentials or missing user input")
            if any(change.target_node_id != self.diagnosis.affected_node_id for change in self.proposed_changes):
                raise ValueError("each proposal must target the diagnosed node")
        return self


class RepairResult(RepairContract):
    workflow_id: Identifier
    workflow_revision_id: Identifier
    final_status: RepairStatus
    repair_attempts: Annotated[
        tuple[RepairAttempt, ...], Field(max_length=MAX_AUTOMATIC_REPAIR_ATTEMPTS)
    ] = ()
    verification_result: VerificationResult | None = None
    rollback_status: RollbackStatus = RollbackStatus.NOT_REQUIRED
    explanation: DiagnosticText = Field(repr=False)

    @model_validator(mode="after")
    def check_result(self) -> Self:
        for number, attempt in enumerate(self.repair_attempts, start=1):
            if attempt.attempt_number != number:
                raise ValueError("repair attempts must be numbered consecutively from one")
            if attempt.verification_status == VerificationStatus.PASSED and number != len(self.repair_attempts):
                raise ValueError("a verified attempt must be the final attempt")

        last_attempt = self.repair_attempts[-1] if self.repair_attempts else None
        if self.verification_result:
            if not last_attempt or last_attempt.verification_status != self.verification_result.status:
                raise ValueError("verification evidence must match the final attempt status")
            if self.verification_result.candidate_revision_id == self.workflow_revision_id:
                raise ValueError("verification must target a separate candidate revision")

        if self.final_status == RepairStatus.SUCCEEDED:
            if not self.verification_result or self.verification_result.status != VerificationStatus.PASSED:
                raise ValueError("a successful repair requires passing verification evidence")
            if self.rollback_status != RollbackStatus.NOT_REQUIRED:
                raise ValueError("a successful repair cannot have a rollback outcome")
        elif last_attempt and last_attempt.verification_status == VerificationStatus.PASSED:
            raise ValueError("a passed final attempt requires a successful repair result")
        return self
