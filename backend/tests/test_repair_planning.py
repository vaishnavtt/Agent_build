"""Test-only snapshots, policies and replacement adapter for candidate repair."""

import json
from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Annotated, Literal

import pytest
from pydantic import Field, TypeAdapter

from app.schemas.repair import DiagnosisResult, FailureInformation, VerificationStatus
from app.services.repair import planning
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
from app.services.repair.planning import (
    ConfigurationLayout,
    FieldPurpose,
    RepairPlanner,
    ReplacementProvenance,
    ReplacementSource,
    ScalarFieldPolicy,
    TrustedReplacement,
    UnsafeRepair,
)
from app.services.repair.service import WorkflowSnapshot


@dataclass
class FixtureReplacementProvider:
    value: object = "json"
    available: bool = True
    source_revision_id: str = "working-revision"
    source: ReplacementSource = ReplacementSource.LAST_KNOWN_WORKING_REVISION
    mismatched_target: dict | None = None

    def get_replacement(self, target):
        if not self.available:
            return None
        provenance = ReplacementProvenance(
            replace(target, **(self.mismatched_target or {})),
            self.source_revision_id,
            self.source,
        )
        return TrustedReplacement(self.value, provenance)


@dataclass(frozen=True)
class RepairCase:
    failure: FailureInformation
    diagnosis: DiagnosisResult
    context: DiagnosisContext
    snapshot: WorkflowSnapshot
    policy: ScalarFieldPolicy
    provider: FixtureReplacementProvider

    @property
    def inputs(self):
        return self.failure, self.diagnosis, self.context, self.snapshot

    @property
    def planner(self):
        return RepairPlanner({"Output": (self.policy,)}, self.provider)


def make_case(
    configuration=None,
    *,
    node_type="Output",
    field_name="outputFormat",
    value_schema=Literal["json", "markdown"],
    layout=ConfigurationLayout.NODE_CONFIG,
):
    configuration = {} if configuration is None else configuration
    definition = ConfigurationFieldDefinition(field_name, required=True, allow_automatic_repair=True)
    policy = ScalarFieldPolicy(definition, "output-schema-v1", layout, FieldPurpose.DATA, TypeAdapter(value_schema))
    if layout == ConfigurationLayout.NODE_CONFIG:
        node = {"id": "output", "type": node_type, "config": configuration}
    else:
        node = {
            "id": "output", "type": "customWorkflow",
            "data": {"componentType": node_type, "config": configuration},
        }
    graph = {
        "metadata": {"id": "workflow-1", "title": "Report", "tags": ["documents"]},
        "nodes": [
            {"id": "input", "type": "Input", "config": {"samples": [{"active": True}]}},
            node,
        ],
        "edges": [{"source": "input", "target": "output", "data": {"keys": ["text"]}}],
        "configuration": {"autoRepairEnabled": True, "approvalRequired": True},
        "requirements": {"prompt": "Summarize the document."},
        "testCriteria": [{"id": "test-1", "expected": "valid JSON"}],
    }
    failure = FailureInformation(
        workflow_id="workflow-1",
        workflow_revision_id="revision-2",
        execution_run_id="run-1",
        failed_node_id="output",
        error_code=DiagnosticCode.MISSING_REQUIRED_CONFIGURATION,
        error_message="Required configuration missing.",
        failed_test_ids=("test-1",),
    )
    context = DiagnosisContext(
        "workflow-1", "revision-2", "run-1",
        (DiagnosticNode("output", node_type, configuration),),
        ConfigurationEvidence("output", field_name, True),
    )
    requirements = OriginalRequirements(
        "Summarize the document.", (AcceptanceCriterion("test-1", "Return valid JSON."),)
    )
    diagnosis = RuleBasedDiagnoser({node_type: (definition,)}).diagnose(failure, requirements, context=context)
    snapshot = WorkflowSnapshot("workflow-1", "revision-2", json.dumps(graph))
    return RepairCase(failure, diagnosis, context, snapshot, policy, FixtureReplacementProvider())


@pytest.fixture
def case():
    return make_case()


def test_plan_uses_phase_two_diagnosis_and_trusted_provenance(case):
    planner = case.planner
    plan = planner.plan(*case.inputs)

    planner.validate(plan, *case.inputs)
    assert plan.proposal.model_dump(mode="json") == {
        "target_node_id": "output",
        "operation": "set_configuration_field",
        "target_configuration_field": "outputFormat",
        "original_value": None,
        "proposed_value": "json",
        "reason": "Restore the approved setting from the trusted working revision.",
    }
    assert plan.provenance.target == plan.target
    assert plan.provenance.source_revision_id == "working-revision"
    assert plan.target.schema_id == "output-schema-v1"
    assert plan.original_field_present is False


@pytest.mark.parametrize(
    ("configuration", "present", "original"),
    [({}, False, None), ({"outputFormat": None}, True, None), ({"outputFormat": " \t"}, True, " \t")],
)
def test_plan_and_apply_preserve_distinct_missing_field_states(configuration, present, original):
    case = make_case(configuration)
    plan = case.planner.plan(*case.inputs)
    candidate = case.planner.apply(plan, *case.inputs)

    assert plan.original_field_present is present
    assert plan.proposal.original_value == original
    assert candidate.graph["nodes"][1]["config"]["outputFormat"] == "json"
    assert json.loads(case.snapshot.graph_json)["nodes"][1]["config"] == configuration


@pytest.mark.parametrize(("field_name", "value"), [("enabled", False), ("retryCount", 0)])
def test_falsy_values_are_valid_replacements_and_cannot_be_overwritten(field_name, value):
    case = make_case(field_name=field_name, value_schema=type(value))
    case.provider.value = value
    plan = case.planner.plan(*case.inputs)
    candidate = case.planner.apply(plan, *case.inputs)
    assert candidate.graph["nodes"][1]["config"][field_name] is value

    filled_case = make_case({field_name: value}, field_name=field_name, value_schema=type(value))
    with pytest.raises(UnsafeRepair, match="no longer missing"):
        filled_case.planner.plan(filled_case.failure, case.diagnosis, filled_case.context, filled_case.snapshot)


@pytest.mark.parametrize("update", [{"repairable": False}, {"requires_human_intervention": True}])
def test_blocked_diagnosis_cannot_generate_a_plan(case, update):
    case = replace(case, diagnosis=case.diagnosis.model_copy(update=update))
    with pytest.raises(UnsafeRepair, match="diagnosis does not permit"):
        case.planner.plan(*case.inputs)


def test_missing_replacement_rejects_plan(case):
    case.provider.available = False
    with pytest.raises(UnsafeRepair, match="No trusted replacement"):
        case.planner.plan(*case.inputs)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("workflow_id", "other-workflow"), ("workflow_revision_id", "other-revision"),
        ("node_id", "other-node"), ("node_type", "Input"),
        ("field_name", "otherField"), ("schema_id", "different-schema"),
        ("layout", ConfigurationLayout.NODE_DATA_CONFIG),
    ],
)
def test_replacement_provenance_must_match_entire_target(case, name, value):
    case.provider.mismatched_target = {name: value}
    with pytest.raises(UnsafeRepair, match="provenance"):
        case.planner.plan(*case.inputs)


@pytest.mark.parametrize("update", [{"source": "unverified"}, {"source_revision_id": "revision-2"}, {"source_revision_id": ""}])
def test_replacement_provenance_must_identify_an_approved_source(case, update):
    case = replace(case, provider=replace(case.provider, **update))
    with pytest.raises(UnsafeRepair, match="provenance"):
        case.planner.plan(*case.inputs)


@pytest.mark.parametrize("value", [False, 0, "xml", None, " ", {"format": "json"}, float("inf")])
def test_rejects_invalid_replacement_values(case, value):
    case.provider.value = value
    with pytest.raises(UnsafeRepair, match="replacement"):
        case.planner.plan(*case.inputs)


@pytest.mark.parametrize("value", [True, "0", -1, 4, 1.0])
def test_replacement_must_satisfy_strict_numeric_constraints(value):
    case = make_case(field_name="retryCount", value_schema=Annotated[int, Field(ge=0, le=3)])
    case.provider.value = value
    with pytest.raises(UnsafeRepair, match="approved field schema"):
        case.planner.plan(*case.inputs)


@pytest.mark.parametrize(
    "purpose",
    [
        FieldPurpose.CREDENTIAL, FieldPurpose.SECURITY, FieldPurpose.EXECUTABLE,
        FieldPurpose.REQUIREMENT, FieldPurpose.TEST_CRITERION,
    ],
)
def test_explicit_policy_blocks_protected_field_purposes(case, purpose):
    case = replace(case, policy=replace(case.policy, purpose=purpose))
    with pytest.raises(UnsafeRepair, match="policy prohibits"):
        case.planner.plan(*case.inputs)


@pytest.mark.parametrize(
    "field_name", ["api_key", "providerApiKey", "clientSecret", "approvalRequired", "script", "testCriteria"]
)
def test_common_protected_fields_are_blocked_even_if_marked_as_data(field_name):
    case = make_case(field_name=field_name)
    with pytest.raises(UnsafeRepair, match="policy prohibits"):
        case.planner.plan(*case.inputs)


def test_approval_node_settings_are_excluded_from_automatic_repair():
    case = make_case(node_type="Human Approval", field_name="defaultAction")
    planner = RepairPlanner({"Human Approval": (case.policy,)}, case.provider)
    with pytest.raises(UnsafeRepair, match="policy prohibits"):
        planner.plan(*case.inputs)


def test_requires_unambiguous_explicit_field_approval(case):
    for policies in ({}, {"Output": (case.policy, case.policy)}):
        with pytest.raises(UnsafeRepair, match="unapproved or has an ambiguous mapping"):
            RepairPlanner(policies, case.provider).plan(*case.inputs)

    denied = replace(case.policy.definition, allow_automatic_repair=False)
    case = replace(case, policy=replace(case.policy, definition=denied))
    with pytest.raises(UnsafeRepair, match="policy prohibits"):
        case.planner.plan(*case.inputs)


@pytest.mark.parametrize("target_count", [0, 2])
def test_snapshot_node_id_must_resolve_uniquely(case, target_count):
    graph = json.loads(case.snapshot.graph_json)
    graph["nodes"] = graph["nodes"][:1] + [graph["nodes"][1]] * target_count
    case = replace(case, snapshot=replace(case.snapshot, graph_json=json.dumps(graph)))
    with pytest.raises(UnsafeRepair, match="missing or ambiguous in the original workflow"):
        case.planner.plan(*case.inputs)


@pytest.mark.parametrize("key", ["workflow_id", "revision_id"])
def test_snapshot_identity_must_match_failure_and_context(case, key):
    case = replace(case, snapshot=replace(case.snapshot, **{key: "wrong"}))
    with pytest.raises(UnsafeRepair, match="identity does not match"):
        case.planner.plan(*case.inputs)


def test_snapshot_rejects_conflicting_embedded_identity(case):
    graph = json.loads(case.snapshot.graph_json)
    graph["metadata"]["id"] = "different-workflow"
    case = replace(case, snapshot=replace(case.snapshot, graph_json=json.dumps(graph)))
    with pytest.raises(UnsafeRepair, match="document identity"):
        case.planner.plan(*case.inputs)


@pytest.mark.parametrize("new_configuration", [{"outputFormat": None}, {"outputFormat": " "}, {"outputFormat": "markdown"}])
def test_application_rechecks_absence_and_rejects_stale_proposals(case, new_configuration):
    plan = case.planner.plan(*case.inputs)
    updated = make_case(new_configuration)
    with pytest.raises(UnsafeRepair, match="expected field state has changed|no longer missing"):
        case.planner.apply(plan, updated.failure, case.diagnosis, updated.context, updated.snapshot)


def test_application_rechecks_provider_even_if_plan_was_validated(case):
    planner = case.planner
    plan = planner.plan(*case.inputs)
    planner.validate(plan, *case.inputs)
    case.provider.value = "markdown"
    with pytest.raises(UnsafeRepair, match="no longer matches"):
        planner.apply(plan, *case.inputs)


@pytest.mark.parametrize(
    ("update", "message"),
    [
        ({"operation": "execute_code"}, "Unsupported repair operation"),
        ({"target_node_id": "input"}, "proposal target"),
        ({"target_configuration_field": "testCriteria"}, "proposal target"),
        ({"original_value": " "}, "expected field state"),
        ({"proposed_value": "markdown"}, "no longer matches"),
    ],
)
def test_revalidates_tampered_proposals(case, update, message):
    plan = case.planner.plan(*case.inputs)
    plan = replace(plan, proposal=plan.proposal.model_copy(update=update))
    with pytest.raises(UnsafeRepair, match=message):
        case.planner.apply(plan, *case.inputs)


def test_rejects_conflicting_configuration_paths(case):
    graph = json.loads(case.snapshot.graph_json)
    graph["nodes"][1]["data"] = {"componentType": "Output", "config": {"outputFormat": "markdown"}}
    case = replace(case, snapshot=replace(case.snapshot, graph_json=json.dumps(graph)))
    with pytest.raises(UnsafeRepair, match="configuration path"):
        case.planner.plan(*case.inputs)


def test_rejects_conflicting_instruction_field_policies():
    case = make_case(node_type="LLM", field_name="instructions")
    approved = replace(case.policy, definition=replace(case.policy.definition, is_instruction_field=True))
    alternate = replace(approved, definition=replace(approved.definition, name="systemPrompt"))
    planner = RepairPlanner({"LLM": (approved, alternate)}, case.provider)
    with pytest.raises(UnsafeRepair, match="ambiguous instructions mapping"):
        planner.plan(*case.inputs)


def test_uses_nested_layout_only_when_explicitly_approved():
    case = make_case(layout=ConfigurationLayout.NODE_DATA_CONFIG)
    plan = case.planner.plan(*case.inputs)
    candidate = case.planner.apply(plan, *case.inputs)
    assert candidate.graph["nodes"][1]["data"]["config"]["outputFormat"] == "json"
    assert "config" not in candidate.graph["nodes"][1]

    wrong_layout = replace(case, policy=replace(case.policy, layout=ConfigurationLayout.NODE_CONFIG))
    with pytest.raises(UnsafeRepair, match="configuration path"):
        wrong_layout.planner.plan(*wrong_layout.inputs)


def test_preserves_entire_original_and_returns_an_independent_unverified_candidate(case):
    original_json = case.snapshot.graph_json
    original = json.loads(original_json)
    expected = deepcopy(original)
    expected["nodes"][1]["config"]["outputFormat"] = "json"
    planner = case.planner
    plan = planner.plan(*case.inputs)
    candidate = planner.apply(plan, *case.inputs)

    assert candidate.graph == expected
    assert case.snapshot.graph_json == original_json
    assert candidate.graph["requirements"] == original["requirements"]
    assert candidate.graph["testCriteria"] == original["testCriteria"]
    assert candidate.execution_status == VerificationStatus.NOT_RUN
    assert candidate.verification_status == VerificationStatus.NOT_RUN
    assert not hasattr(candidate, "final_status")

    candidate.graph["nodes"][0]["config"]["samples"][0]["active"] = False
    candidate.graph["edges"][0]["data"]["keys"].append("extra")
    candidate.graph["metadata"]["tags"].append("changed")
    assert planner.apply(plan, *case.inputs).graph == expected
    assert case.snapshot.graph_json == original_json


def test_rejects_an_unexpected_additional_change(case, monkeypatch):
    def faulty_copy(graph):
        candidate = deepcopy(graph)
        candidate["configuration"]["approvalRequired"] = False
        return candidate

    monkeypatch.setattr(planning, "deepcopy", faulty_copy)
    plan = case.planner.plan(*case.inputs)
    with pytest.raises(UnsafeRepair, match="changes outside the approved field"):
        case.planner.apply(plan, *case.inputs)


def test_plan_and_candidate_are_deterministic(case):
    planner = case.planner
    first = planner.plan(*case.inputs)
    second = planner.plan(*case.inputs)
    assert first == second
    assert planner.apply(first, *case.inputs) == planner.apply(second, *case.inputs)
