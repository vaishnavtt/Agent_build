"""Plan and apply one approved scalar repair to an isolated workflow candidate."""

import json
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from typing import Any, Protocol

from pydantic import TypeAdapter, ValidationError

from app.schemas.repair import (
    ConfigurationField,
    ConfigurationValue,
    DiagnosisResult,
    FailureCategory,
    FailureInformation,
    RepairOperation,
    RepairProposal,
    VerificationStatus,
)
from app.services.repair.diagnosis import (
    ConfigurationFieldDefinition,
    DiagnosisContext,
    DiagnosticCode,
)
from app.services.repair.service import WorkflowSnapshot


class UnsafeRepair(ValueError):
    """An input did not satisfy Phase 3's repair policy."""


class ConfigurationLayout(StrEnum):
    NODE_CONFIG = "node_config"
    NODE_DATA_CONFIG = "node_data_config"


class FieldPurpose(StrEnum):
    DATA = "data"
    CREDENTIAL = "credential"
    SECURITY = "security"
    EXECUTABLE = "executable"
    REQUIREMENT = "requirement"
    TEST_CRITERION = "test_criterion"


class ReplacementSource(StrEnum):
    LAST_KNOWN_WORKING_REVISION = "last_known_working_revision"


@dataclass(frozen=True)
class ScalarFieldPolicy:
    definition: ConfigurationFieldDefinition
    schema_id: str
    layout: ConfigurationLayout
    purpose: FieldPurpose
    value_schema: TypeAdapter


@dataclass(frozen=True)
class RepairTarget:
    workflow_id: str
    workflow_revision_id: str
    node_id: str
    node_type: str
    field_name: str
    schema_id: str
    layout: ConfigurationLayout


@dataclass(frozen=True)
class ReplacementProvenance:
    target: RepairTarget
    source_revision_id: str
    source: ReplacementSource


@dataclass(frozen=True)
class TrustedReplacement:
    value: ConfigurationValue = field(repr=False)
    provenance: ReplacementProvenance


class ReplacementProvider(Protocol):
    """Trusted adapter attesting that the value came from the identified working revision.

    The source must be for the same workflow, node, field, and compatible schema
    identified by the target. The planner checks this binding and the value on
    every read. Authenticating revision history is the adapter's responsibility.
    """

    def get_replacement(self, target: RepairTarget) -> TrustedReplacement | None: ...


@dataclass(frozen=True)
class RepairPlan:
    target: RepairTarget
    execution_run_id: str
    snapshot_digest: str
    original_field_present: bool
    proposal: RepairProposal
    provenance: ReplacementProvenance


@dataclass(frozen=True)
class RepairCandidate:
    target: RepairTarget
    graph: dict[str, Any] = field(repr=False)
    execution_status: VerificationStatus = field(default=VerificationStatus.NOT_RUN, init=False)
    verification_status: VerificationStatus = field(default=VerificationStatus.NOT_RUN, init=False)


@dataclass(frozen=True)
class _RepairState:
    target: RepairTarget
    policy: ScalarFieldPolicy
    graph: dict[str, Any] = field(repr=False)
    node_index: int
    original_field_present: bool
    original_value: ConfigurationValue = field(repr=False)
    snapshot_digest: str


_FIELD_NAME = TypeAdapter(ConfigurationField)
_PROTECTED_FIELDS = frozenset({
    "credential", "credentials", "secret", "secrets", "token", "authorization",
    "requireapproval", "requiresapproval", "approvalrequired", "approvalpolicy",
    "securitypolicy", "permissions", "allowlist", "denylist",
    "code", "script", "command", "executable", "endpoint",
    "requirements", "acceptancecriteria", "testcriteria", "testcases", "assertions",
})
_CREDENTIAL_SUFFIXES = (
    "apikey", "password", "secret", "accesstoken", "refreshtoken", "privatekey", "credential",
)


class RepairPlanner:
    def __init__(
        self, policies: Mapping[str, tuple[ScalarFieldPolicy, ...]], provider: ReplacementProvider
    ) -> None:
        self._policies = {node_type: tuple(fields) for node_type, fields in policies.items()}
        self._provider = provider

    def plan(
        self,
        failure: FailureInformation,
        diagnosis: DiagnosisResult,
        context: DiagnosisContext,
        snapshot: WorkflowSnapshot,
    ) -> RepairPlan:
        state = self._inspect(failure, diagnosis, context, snapshot)
        replacement = self._replacement_for(state)
        return RepairPlan(
            target=state.target,
            execution_run_id=failure.execution_run_id,
            snapshot_digest=state.snapshot_digest,
            original_field_present=state.original_field_present,
            proposal=RepairProposal(
                target_node_id=state.target.node_id,
                operation=RepairOperation.SET_CONFIGURATION_FIELD,
                target_configuration_field=state.target.field_name,
                original_value=state.original_value,
                proposed_value=replacement.value,
                reason="Restore the approved setting from the trusted working revision.",
            ),
            provenance=replacement.provenance,
        )

    def validate(
        self,
        plan: RepairPlan,
        failure: FailureInformation,
        diagnosis: DiagnosisResult,
        context: DiagnosisContext,
        snapshot: WorkflowSnapshot,
    ) -> None:
        self._validate_plan(plan, failure, diagnosis, context, snapshot)

    def apply(
        self,
        plan: RepairPlan,
        failure: FailureInformation,
        diagnosis: DiagnosisResult,
        context: DiagnosisContext,
        snapshot: WorkflowSnapshot,
    ) -> RepairCandidate:
        state = self._validate_plan(plan, failure, diagnosis, context, snapshot)
        candidate = deepcopy(state.graph)
        configuration = _configuration(candidate["nodes"][state.node_index], state.target)
        configuration[state.target.field_name] = plan.proposal.proposed_value

        # Reverse the one permitted edit and compare the entire document, with
        # JSON types preserved. Restore the edit only after the comparison passes.
        if state.original_field_present:
            configuration[state.target.field_name] = state.original_value
        else:
            del configuration[state.target.field_name]
        if _canonical_json(candidate) != _canonical_json(state.graph):
            raise UnsafeRepair("The candidate contains changes outside the approved field.")
        configuration[state.target.field_name] = plan.proposal.proposed_value
        return RepairCandidate(state.target, candidate)

    def _validate_plan(
        self,
        plan: RepairPlan,
        failure: FailureInformation,
        diagnosis: DiagnosisResult,
        context: DiagnosisContext,
        snapshot: WorkflowSnapshot,
    ) -> _RepairState:
        state = self._inspect(failure, diagnosis, context, snapshot)
        proposal = plan.proposal
        if proposal.operation != RepairOperation.SET_CONFIGURATION_FIELD:
            raise UnsafeRepair("Unsupported repair operation.")
        if (
            plan.target != state.target
            or plan.execution_run_id != failure.execution_run_id
            or proposal.target_node_id != state.target.node_id
            or proposal.target_configuration_field != state.target.field_name
        ):
            raise UnsafeRepair("The proposal target does not match the trusted failure and field policy.")
        if (
            plan.snapshot_digest != state.snapshot_digest
            or plan.original_field_present is not state.original_field_present
            or not _same_scalar(proposal.original_value, state.original_value)
        ):
            raise UnsafeRepair("The original snapshot or expected field state has changed.")
        replacement = self._replacement_for(state)
        if plan.provenance != replacement.provenance or not _same_scalar(proposal.proposed_value, replacement.value):
            raise UnsafeRepair("The proposed value or provenance no longer matches the trusted replacement.")
        return state

    def _inspect(
        self,
        failure: FailureInformation,
        diagnosis: DiagnosisResult,
        context: DiagnosisContext,
        snapshot: WorkflowSnapshot,
    ) -> _RepairState:
        if (
            not diagnosis.repairable
            or diagnosis.requires_human_intervention
            or diagnosis.category != FailureCategory.CONFIGURATION
            or failure.error_code not in (
                DiagnosticCode.MISSING_REQUIRED_CONFIGURATION,
                DiagnosticCode.EMPTY_LLM_INSTRUCTIONS,
            )
        ):
            raise UnsafeRepair("The diagnosis does not permit a missing-configuration repair.")
        if not (
            failure.workflow_id == context.workflow_id == snapshot.workflow_id
            and failure.workflow_revision_id == context.workflow_revision_id == snapshot.revision_id
            and failure.execution_run_id == context.execution_run_id
        ):
            raise UnsafeRepair("Workflow, revision, or run identity does not match.")

        node_id = diagnosis.affected_node_id
        field_name = diagnosis.affected_configuration_field
        evidence = context.configuration_evidence
        if (
            not node_id
            or not field_name
            or node_id != failure.failed_node_id
            or evidence is None
            or (evidence.node_id, evidence.field_name) != (node_id, field_name)
            or not evidence.has_trusted_replacement
        ):
            raise UnsafeRepair("The diagnosis and trusted evidence do not identify the same node and field.")

        diagnostic_nodes = [node for node in context.nodes if node.node_id == node_id]
        if len(diagnostic_nodes) != 1:
            raise UnsafeRepair("The target node ID is missing or ambiguous in the trusted context.")
        diagnostic_node = diagnostic_nodes[0]
        policy = self._policy_for(diagnostic_node.node_type, field_name, failure.error_code)
        target = RepairTarget(
            snapshot.workflow_id, snapshot.revision_id, node_id, diagnostic_node.node_type,
            field_name, policy.schema_id, policy.layout,
        )
        graph = _read_snapshot(snapshot)
        node_indexes = [index for index, node in enumerate(graph["nodes"]) if node["id"] == node_id]
        if len(node_indexes) != 1:
            raise UnsafeRepair("The target node ID is missing or ambiguous in the original workflow.")
        node_index = node_indexes[0]
        configuration = _configuration(graph["nodes"][node_index], target)
        present = field_name in configuration
        original = configuration.get(field_name)
        if present != (field_name in diagnostic_node.configuration) or not _same_scalar(
            original, diagnostic_node.configuration.get(field_name)
        ):
            raise UnsafeRepair("The original field state disagrees with the trusted diagnostic context.")
        if not policy.definition.is_missing(original):
            raise UnsafeRepair("The original configuration field is no longer missing.")
        digest = sha256(_canonical_json(graph).encode("ascii")).hexdigest()
        return _RepairState(target, policy, graph, node_index, present, original, digest)

    def _policy_for(self, node_type: str, field_name: str, error_code: str) -> ScalarFieldPolicy:
        try:
            _FIELD_NAME.validate_python(field_name, strict=True)
        except ValidationError:
            raise UnsafeRepair("The target is not an approved scalar field name.") from None
        policies = self._policies.get(node_type, ())
        matching = [policy for policy in policies if policy.definition.name == field_name]
        if len(matching) != 1:
            raise UnsafeRepair("The field is unapproved or has an ambiguous mapping.")
        policy = matching[0]
        definition = policy.definition
        if error_code == DiagnosticCode.EMPTY_LLM_INSTRUCTIONS or definition.is_instruction_field:
            instructions = [item for item in policies if item.definition.is_instruction_field]
            if instructions != [policy]:
                raise UnsafeRepair("The approved schema has an ambiguous instructions mapping.")
        normalized_field = field_name.replace("_", "").lower()
        if (
            not policy.schema_id.strip()
            or not definition.required
            or not definition.allow_automatic_repair
            or policy.purpose != FieldPurpose.DATA
            or node_type == "Human Approval"
            or normalized_field in _PROTECTED_FIELDS
            or normalized_field.endswith(_CREDENTIAL_SUFFIXES)
        ):
            raise UnsafeRepair("The field policy prohibits automatic repair.")
        return policy

    def _replacement_for(self, state: _RepairState) -> TrustedReplacement:
        replacement = self._provider.get_replacement(state.target)
        if replacement is None:
            raise UnsafeRepair("No trusted replacement was found.")
        provenance = replacement.provenance
        if (
            provenance.target != state.target
            or provenance.source != ReplacementSource.LAST_KNOWN_WORKING_REVISION
            or provenance.source_revision_id.strip() in ("", state.target.workflow_revision_id)
        ):
            raise UnsafeRepair("Replacement provenance does not match the approved source and target.")
        value = replacement.value
        if type(value) not in (str, bool, int, float) or state.policy.definition.is_missing(value):
            raise UnsafeRepair("The replacement must be a usable scalar value.")
        try:
            _canonical_json(value)
            validated = state.policy.value_schema.validate_python(value, strict=True)
        except ValidationError:
            raise UnsafeRepair("The replacement does not satisfy the approved field schema.") from None
        if not _same_scalar(value, validated):
            raise UnsafeRepair("The approved field schema would change the replacement value.")
        return replacement


def _same_scalar(left: object, right: object) -> bool:
    return type(left) is type(right) and left == right


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    if len(pairs) != len(result):
        raise UnsafeRepair("The workflow JSON contains duplicate object keys.")
    return result


def _read_snapshot(snapshot: WorkflowSnapshot) -> dict[str, Any]:
    try:
        graph = json.loads(snapshot.graph_json, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, RecursionError):
        raise UnsafeRepair("The workflow snapshot is not a valid JSON document.") from None
    if not isinstance(graph, dict) or not isinstance(graph.get("nodes"), list):
        raise UnsafeRepair("The workflow snapshot has no usable node list.")
    metadata = graph.get("metadata")
    identities = [graph]
    if isinstance(metadata, dict):
        identities.append(metadata)
    if any("id" in item and item["id"] != snapshot.workflow_id for item in identities):
        raise UnsafeRepair("The workflow document identity does not match the snapshot.")
    if any(not isinstance(node, dict) or not isinstance(node.get("id"), str) for node in graph["nodes"]):
        raise UnsafeRepair("The workflow document contains a node without a stable ID.")
    return graph


def _configuration(node: dict[str, Any], target: RepairTarget) -> dict[str, Any]:
    data = node.get("data")
    nested = isinstance(data, dict) and "config" in data
    if target.layout == ConfigurationLayout.NODE_CONFIG and not nested:
        configuration = node.get("config")
        node_type = node.get("type")
    elif target.layout == ConfigurationLayout.NODE_DATA_CONFIG and nested and "config" not in node:
        configuration = data["config"]
        node_type = data.get("componentType")
    else:
        raise UnsafeRepair("The node configuration path does not match the approved layout.")
    if node_type != target.node_type or not isinstance(configuration, dict):
        raise UnsafeRepair("The node type or configuration object does not match the approved layout.")
    return configuration


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":"))
    except (ValueError, TypeError, RecursionError):
        raise UnsafeRepair("The workflow or replacement contains an unsupported JSON value.") from None
