import pytest
from pydantic import ValidationError

from app.schemas.repair import (
    DiagnosisResult,
    FailureInformation,
    RepairAttempt,
    RepairProposal,
    RepairResult,
    VerificationResult,
    VerificationStatus,
)


@pytest.fixture
def failure_data():
    return {
        "workflow_id": "workflow-1",
        "workflow_revision_id": "revision-1",
        "execution_run_id": "run-1",
        "failed_node_id": "node-1",
        "error_code": "MISSING_SETTING",
        "error_message": "Required configuration is missing.",
        "safe_diagnostic_evidence": ["The configured output format is absent."],
        "failed_test_ids": ["format-test"],
    }


@pytest.fixture
def attempt_data():
    return {
        "attempt_number": 1,
        "diagnosis": {
            "category": "configuration",
            "affected_node_id": "node-1",
            "root_cause": "The output format is missing.",
            "supporting_evidence": ["The original setting came from a working revision."],
            "repairable": True,
            "requires_human_intervention": False,
        },
        "proposed_changes": [
            {
                "target_node_id": "node-1",
                "operation": "set_configuration_field",
                "target_configuration_field": "outputFormat",
                "original_value": None,
                "proposed_value": "json",
                "reason": "Restore the output format from the working revision.",
            }
        ],
        "verification_status": "passed",
    }


@pytest.fixture
def verification_data():
    return {
        "candidate_revision_id": "revision-2",
        "structural_validation": "passed",
        "execution": {"run_id": "run-2", "status": "passed"},
        "required_failed_test_ids": ["format-test"],
        "required_regression_test_ids": ["content-test"],
        "failed_test_reruns": [{"test_id": "format-test", "status": "passed"}],
        "regression_test_reruns": [{"test_id": "content-test", "status": "passed"}],
    }


@pytest.fixture
def successful_result_data(attempt_data, verification_data):
    return {
        "workflow_id": "workflow-1",
        "workflow_revision_id": "revision-1",
        "final_status": "succeeded",
        "repair_attempts": [attempt_data],
        "verification_result": verification_data,
        "explanation": "Validation, candidate execution, and required tests passed.",
    }


def test_failure_record_keeps_redacted_evidence_and_test_ids(failure_data):
    failure = FailureInformation.model_validate(failure_data)
    assert failure.failed_node_id == "node-1"
    assert failure.failed_test_ids == ("format-test",)
    assert failure.safe_diagnostic_evidence == ("The configured output format is absent.",)
    assert failure.error_message not in repr(failure)
    assert failure.safe_diagnostic_evidence[0] not in repr(failure)


def test_workflow_level_failure_can_omit_node_and_test_ids(failure_data):
    del failure_data["failed_node_id"], failure_data["failed_test_ids"]
    failure = FailureInformation.model_validate(failure_data)
    assert failure.failed_node_id is None
    assert failure.failed_test_ids == ()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("workflow_id", ""),
        ("workflow_revision_id", " "),
        ("execution_run_id", None),
        ("failed_node_id", " "),
        ("error_code", ""),
        ("error_message", " "),
        ("safe_diagnostic_evidence", [" "]),
        ("failed_test_ids", [" "]),
        ("raw_log", "unexpected"),
    ],
)
def test_rejects_invalid_failure_record(failure_data, field, value):
    failure_data[field] = value
    with pytest.raises(ValidationError, match=field):
        FailureInformation.model_validate(failure_data)


def test_requires_workflow_revision(failure_data):
    del failure_data["workflow_revision_id"]
    with pytest.raises(ValidationError, match="workflow_revision_id"):
        FailureInformation.model_validate(failure_data)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("operation", "execute_code"),
        ("operation", "delete_node"),
        ("target_configuration_field", "workflow.nodes[0]"),
        ("proposed_value", {"nested": True}),
    ],
)
def test_rejects_unsupported_repair_proposal(attempt_data, field, value):
    proposal = attempt_data["proposed_changes"][0]
    proposal[field] = value
    with pytest.raises(ValidationError, match=field):
        RepairProposal.model_validate(proposal)


@pytest.mark.parametrize("attempt_number", [0, 3, True, "1"])
def test_rejects_invalid_attempt_number(attempt_data, attempt_number):
    attempt_data["attempt_number"] = attempt_number
    with pytest.raises(ValidationError, match="attempt_number"):
        RepairAttempt.model_validate(attempt_data)


@pytest.mark.parametrize("category", ["credentials", "missing_input"])
def test_blocks_automatic_patches_for_missing_credentials_or_input(attempt_data, category):
    attempt_data["diagnosis"]["category"] = category
    with pytest.raises(ValidationError, match="credentials or missing user input"):
        RepairAttempt.model_validate(attempt_data)


def test_rejects_a_proposal_for_a_different_node(attempt_data):
    attempt_data["proposed_changes"][0]["target_node_id"] = "other-node"
    with pytest.raises(ValidationError, match="diagnosed node"):
        RepairAttempt.model_validate(attempt_data)


def test_rejects_automatic_changes_when_human_intervention_is_required(attempt_data):
    attempt_data["diagnosis"]["requires_human_intervention"] = True
    attempt_data["diagnosis"]["category"] = "unknown"
    assert DiagnosisResult.model_validate(attempt_data["diagnosis"]).requires_human_intervention
    with pytest.raises(ValidationError, match="without human intervention"):
        RepairAttempt.model_validate(attempt_data)


def test_success_requires_verified_candidate_and_supports_round_trip(successful_result_data):
    result = RepairResult.model_validate(successful_result_data)
    assert result.verification_result.status == VerificationStatus.PASSED
    assert result.repair_attempts[0].proposed_changes[0].proposed_value == "json"
    assert RepairResult.model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("verification_result", None),
        ("repair_attempts", []),
        ("rollback_status", "restored"),
    ],
)
def test_rejects_invalid_success_state(successful_result_data, field, value):
    successful_result_data[field] = value
    with pytest.raises(ValidationError):
        RepairResult.model_validate(successful_result_data)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("execution", None),
        ("structural_validation", "failed"),
        ("failed_test_reruns", []),
        ("regression_test_reruns", [{"test_id": "content-test", "status": "failed"}]),
        ("candidate_revision_id", "revision-1"),
    ],
)
def test_rejects_success_with_incomplete_or_failed_verification(successful_result_data, field, value):
    successful_result_data["verification_result"][field] = value
    with pytest.raises(ValidationError):
        RepairResult.model_validate(successful_result_data)


def test_rejects_unrequested_test_evidence(verification_data):
    verification_data["regression_test_reruns"][0]["test_id"] = "different-test"
    with pytest.raises(ValidationError, match="required group"):
        VerificationResult.model_validate(verification_data)


def test_rejects_more_than_two_attempts(successful_result_data, attempt_data):
    successful_result_data["repair_attempts"] = [attempt_data] * 3
    with pytest.raises(ValidationError, match="at most 2"):
        RepairResult.model_validate(successful_result_data)


def test_accepts_verified_second_attempt_after_failed_attempt(successful_result_data, attempt_data):
    unsuccessful = {
        **attempt_data,
        "verification_status": "failed",
        "failure_reason": "The first candidate did not pass regression testing.",
    }
    successful_result_data["repair_attempts"] = [
        unsuccessful,
        {**attempt_data, "attempt_number": 2},
    ]
    result = RepairResult.model_validate(successful_result_data)
    assert result.repair_attempts[1].attempt_number == 2
