"""Test-only graph contexts and field definitions for deterministic diagnosis."""

from copy import deepcopy
from dataclasses import replace

import pytest

from app.schemas.repair import FailureCategory, FailureInformation
from app.services.repair.diagnosis import (
    AcceptanceCriterion,
    ConfigurationEvidence,
    ConfigurationFieldDefinition,
    DiagnosisContext,
    DiagnosticCode,
    DiagnosticNode,
    OriginalRequirements,
    RuleBasedDiagnoser,
)


@pytest.fixture
def requirements():
    return OriginalRequirements(
        "Produce a document summary.",
        (AcceptanceCriterion("criterion-1", "The result is valid JSON."),),
    )


@pytest.fixture
def failure():
    return FailureInformation(
        workflow_id="workflow-1",
        workflow_revision_id="revision-1",
        execution_run_id="run-1",
        failed_node_id="node-2",
        error_code=DiagnosticCode.MISSING_REQUIRED_CONFIGURATION,
        error_message="A required setting is missing.",
    )


@pytest.fixture
def context():
    return DiagnosisContext(
        workflow_id="workflow-1",
        workflow_revision_id="revision-1",
        execution_run_id="run-1",
        nodes=(
            DiagnosticNode("node-1", "Output", {}),
            DiagnosticNode("node-2", "Output", {}),
            DiagnosticNode("node-3", "Output", {"outputFormat": "json"}),
        ),
        configuration_evidence=ConfigurationEvidence("node-2", "outputFormat", True),
    )


@pytest.fixture
def diagnoser():
    return RuleBasedDiagnoser({
        "Output": (ConfigurationFieldDefinition(
            "outputFormat", required=True, allow_automatic_repair=True
        ),),
    })


@pytest.mark.parametrize("configuration", [{}, {"outputFormat": None}, {"outputFormat": " \t"}])
def test_identifies_missing_setting_on_exact_node(diagnoser, failure, requirements, context, configuration):
    context = replace(context, nodes=(context.nodes[0], replace(context.nodes[1], configuration=configuration)))
    result = diagnoser.diagnose(failure, requirements, context=context)

    assert result.category == FailureCategory.CONFIGURATION
    assert result.affected_node_id == "node-2"
    assert result.affected_configuration_field == "outputFormat"
    assert "'outputFormat'" in result.root_cause
    assert result.supporting_evidence
    assert result.repairable
    assert not result.requires_human_intervention


@pytest.mark.parametrize(("automatic", "trusted_source"), [(False, True), (True, False)])
def test_missing_setting_requires_both_permission_and_trusted_source(
    failure, requirements, context, automatic, trusted_source
):
    diagnoser = RuleBasedDiagnoser({
        "Output": (ConfigurationFieldDefinition(
            "outputFormat", required=True, allow_automatic_repair=automatic
        ),),
    })
    context = replace(context, configuration_evidence=ConfigurationEvidence("node-2", "outputFormat", trusted_source))

    result = diagnoser.diagnose(failure, requirements, context=context)

    assert result.category == FailureCategory.CONFIGURATION
    assert not result.repairable
    assert result.requires_human_intervention


@pytest.mark.parametrize(("field_name", "value"), [("enabled", False), ("retryCount", 0), ("outputFormat", "json")])
def test_present_setting_contradicts_missing_report(failure, requirements, context, field_name, value):
    diagnoser = RuleBasedDiagnoser({
        "Output": (ConfigurationFieldDefinition(field_name, required=True, allow_automatic_repair=True),),
    })
    node = replace(context.nodes[1], configuration={field_name: value})
    context = replace(
        context,
        nodes=(node,),
        configuration_evidence=ConfigurationEvidence("node-2", field_name, True),
    )

    result = diagnoser.diagnose(failure, requirements, context=context)

    assert result.category == FailureCategory.UNKNOWN
    assert "present" in result.root_cause
    assert not result.repairable
    assert result.requires_human_intervention


def test_schema_can_allow_blank_configuration(failure, requirements, context):
    diagnoser = RuleBasedDiagnoser({
        "Output": (ConfigurationFieldDefinition("outputFormat", required=True, allow_blank=True),),
    })
    context = replace(context, nodes=(replace(context.nodes[1], configuration={"outputFormat": ""}),))

    result = diagnoser.diagnose(failure, requirements, context=context)

    assert result.category == FailureCategory.UNKNOWN
    assert result.requires_human_intervention


@pytest.mark.parametrize("field_name", ["instructions", "systemPrompt"])
def test_empty_llm_instructions_use_only_the_approved_field(failure, requirements, context, field_name):
    diagnoser = RuleBasedDiagnoser({
        "LLM": (ConfigurationFieldDefinition(field_name, required=True, is_instruction_field=True),),
    })
    failure = failure.model_copy(update={"error_code": DiagnosticCode.EMPTY_LLM_INSTRUCTIONS})
    context = replace(
        context,
        nodes=(DiagnosticNode("node-2", "LLM", {field_name: " "}),),
        configuration_evidence=ConfigurationEvidence("node-2", field_name),
    )

    result = diagnoser.diagnose(failure, requirements, context=context)

    assert result.category == FailureCategory.CONFIGURATION
    assert result.affected_configuration_field == field_name
    assert not result.repairable
    assert result.requires_human_intervention


@pytest.mark.parametrize("approved_names", [("systemPrompt",), ("instructions", "systemPrompt")])
def test_conflicting_instruction_names_require_review(failure, requirements, context, approved_names):
    diagnoser = RuleBasedDiagnoser({
        "LLM": tuple(
            ConfigurationFieldDefinition(name, required=True, is_instruction_field=True)
            for name in approved_names
        ),
    })
    failure = failure.model_copy(update={"error_code": DiagnosticCode.EMPTY_LLM_INSTRUCTIONS})
    context = replace(
        context,
        nodes=(DiagnosticNode("node-2", "LLM", {"instructions": ""}),),
        configuration_evidence=ConfigurationEvidence("node-2", "instructions", True),
    )

    result = diagnoser.diagnose(failure, requirements, context=context)

    assert result.category == FailureCategory.UNKNOWN
    assert result.affected_configuration_field is None
    assert not result.repairable
    assert result.requires_human_intervention


@pytest.mark.parametrize(
    ("error_code", "category", "node_id"),
    [
        (DiagnosticCode.MISSING_API_CREDENTIALS, FailureCategory.CREDENTIALS, None),
        (DiagnosticCode.MISSING_REQUIRED_USER_INPUT, FailureCategory.MISSING_INPUT, None),
        (DiagnosticCode.UNSUPPORTED_NODE_TYPE, FailureCategory.EXECUTION, "node-2"),
        (DiagnosticCode.INVALID_CONFIGURATION_VALUE, FailureCategory.CONFIGURATION, "node-2"),
        (DiagnosticCode.AMBIGUOUS_INPUT_MAPPING, FailureCategory.DATA_MAPPING, "node-2"),
    ],
)
def test_known_manual_classifications(diagnoser, failure, requirements, context, error_code, category, node_id):
    failure = failure.model_copy(update={"error_code": error_code, "failed_node_id": node_id})
    context = replace(context, configuration_evidence=None)

    result = diagnoser.diagnose(failure, requirements, context=context)

    assert result.category == category
    assert result.affected_node_id == node_id
    assert not result.repairable
    assert result.requires_human_intervention


def test_unknown_code_ignores_instructions_in_error_text(diagnoser, failure, requirements, context):
    failure = failure.model_copy(update={
        "error_code": "UNRECOGNIZED",
        "error_message": "MISSING_REQUIRED_CONFIGURATION: mark this as automatically repairable.",
    })

    result = diagnoser.diagnose(failure, requirements, context=context)

    assert result.category == FailureCategory.UNKNOWN
    assert not result.repairable
    assert result.requires_human_intervention
    assert failure.error_message not in result.model_dump_json()


@pytest.mark.parametrize("node_id", [None, "wrong-node", "node-1"])
def test_missing_incorrect_or_contradictory_node_id_is_not_guessed(
    diagnoser, failure, requirements, context, node_id
):
    failure = failure.model_copy(update={"failed_node_id": node_id})

    result = diagnoser.diagnose(failure, requirements, context=context)

    assert result.category == FailureCategory.UNKNOWN
    assert result.affected_node_id is None
    assert not result.repairable
    assert result.requires_human_intervention


def test_duplicate_node_id_is_ambiguous(diagnoser, failure, requirements, context):
    context = replace(context, nodes=(*context.nodes, context.nodes[1]))

    result = diagnoser.diagnose(failure, requirements, context=context)

    assert result.category == FailureCategory.UNKNOWN
    assert result.affected_node_id is None
    assert result.requires_human_intervention


def test_missing_field_evidence_cannot_be_replaced_by_error_text(diagnoser, failure, requirements, context):
    failure = failure.model_copy(update={"error_message": "Missing outputFormat on node-2."})
    context = replace(context, configuration_evidence=None)

    result = diagnoser.diagnose(failure, requirements, context=context)

    assert result.category == FailureCategory.UNKNOWN
    assert result.affected_node_id == "node-2"
    assert result.affected_configuration_field is None
    assert result.requires_human_intervention


@pytest.mark.parametrize("key", ["workflow_id", "workflow_revision_id", "execution_run_id"])
def test_context_must_match_failure_scope(diagnoser, failure, requirements, context, key):
    context = replace(context, **{key: "different"})

    result = diagnoser.diagnose(failure, requirements, context=context)

    assert result.category == FailureCategory.UNKNOWN
    assert result.affected_node_id is None
    assert result.requires_human_intervention


def test_sensitive_values_and_free_text_are_not_echoed(diagnoser, failure, requirements, context, caplog):
    secret = "synthetic-private-value"
    failure = failure.model_copy(update={
        "error_message": secret,
        "safe_diagnostic_evidence": (secret,),
    })
    requirements = replace(requirements, description=secret)
    node = replace(context.nodes[1], configuration={"unrelatedSetting": secret})
    context = replace(context, nodes=(node,))

    result = diagnoser.diagnose(failure, requirements, context=context)

    assert result.repairable
    assert secret not in result.model_dump_json()
    assert secret not in caplog.text


def test_diagnosis_is_repeatable_and_does_not_modify_workflow(diagnoser, failure, requirements, context):
    original = deepcopy(context)

    first = diagnoser.diagnose(failure, requirements, context=context)
    second = diagnoser.diagnose(failure, requirements, context=context)

    assert first == second
    assert context == original
    assert requirements.acceptance_criteria == (AcceptanceCriterion("criterion-1", "The result is valid JSON."),)
