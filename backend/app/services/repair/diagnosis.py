"""Deterministic workflow diagnosis using revision-scoped, trusted inputs."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from app.schemas.repair import DiagnosisResult, FailureCategory, FailureInformation


@dataclass(frozen=True)
class AcceptanceCriterion:
    criterion_id: str
    description: str


@dataclass(frozen=True)
class OriginalRequirements:
    description: str
    acceptance_criteria: tuple[AcceptanceCriterion, ...]


class DiagnosticCode(StrEnum):
    """Provisional structured codes for the execution and testing adapters."""

    MISSING_REQUIRED_CONFIGURATION = "MISSING_REQUIRED_CONFIGURATION"
    EMPTY_LLM_INSTRUCTIONS = "EMPTY_LLM_INSTRUCTIONS"
    MISSING_API_CREDENTIALS = "MISSING_API_CREDENTIALS"
    MISSING_REQUIRED_USER_INPUT = "MISSING_REQUIRED_USER_INPUT"
    UNSUPPORTED_NODE_TYPE = "UNSUPPORTED_NODE_TYPE"
    INVALID_CONFIGURATION_VALUE = "INVALID_CONFIGURATION_VALUE"
    AMBIGUOUS_INPUT_MAPPING = "AMBIGUOUS_INPUT_MAPPING"


class ExternalDiagnosticFact(StrEnum):
    OUTPUT_SHAPE_MISMATCH = "output_shape_mismatch"
    NODE_EXECUTION_HALTED = "node_execution_halted"
    TEST_ASSERTION_MISMATCH = "test_assertion_mismatch"
    UPSTREAM_OUTPUT_PRESENT = "upstream_output_present"


@dataclass(frozen=True)
class ExternalDiagnosisEvidence:
    """Allowlisted observations and explicit clearance from the trusted run adapter."""

    facts: tuple[ExternalDiagnosticFact, ...]
    cleared_for_external_diagnosis: bool = False


@dataclass(frozen=True)
class ConfigurationFieldDefinition:
    """An exact key in the approved configuration representation for a node type."""

    name: str
    required: bool
    allow_blank: bool = False
    is_instruction_field: bool = False
    allow_automatic_repair: bool = False
    allow_external_diagnosis: bool = False

    def is_missing(self, value: object) -> bool:
        return value is None or (
            isinstance(value, str) and not value.strip() and not self.allow_blank
        )


@dataclass(frozen=True)
class DiagnosticNode:
    node_id: str
    node_type: str
    configuration: Mapping[str, object] = field(repr=False)


@dataclass(frozen=True)
class ConfigurationEvidence:
    """The adapter confirms field identity and may attest a trusted replacement source."""

    node_id: str
    field_name: str
    has_trusted_replacement: bool = False


@dataclass(frozen=True)
class DiagnosisContext:
    """Trusted graph view and structured evidence for the original run and revision."""

    workflow_id: str
    workflow_revision_id: str
    execution_run_id: str
    nodes: tuple[DiagnosticNode, ...]
    configuration_evidence: ConfigurationEvidence | None = None
    external_evidence: ExternalDiagnosisEvidence | None = None


class FailureDiagnoser(Protocol):
    def diagnose(
        self,
        failure: FailureInformation,
        requirements: OriginalRequirements,
        *,
        context: DiagnosisContext,
    ) -> DiagnosisResult:
        """Explain the failure using the supplied evidence and original criteria."""
        ...


_MISSING_CONFIGURATION_CODES = {
    DiagnosticCode.MISSING_REQUIRED_CONFIGURATION,
    DiagnosticCode.EMPTY_LLM_INSTRUCTIONS,
}
_MANUAL_CLASSIFICATIONS = {
    DiagnosticCode.MISSING_API_CREDENTIALS: (
        FailureCategory.CREDENTIALS,
        "The failure record reports missing API credentials. An authorized user must configure them.",
    ),
    DiagnosticCode.MISSING_REQUIRED_USER_INPUT: (
        FailureCategory.MISSING_INPUT,
        "The failure record reports missing required input. The user must supply it.",
    ),
    DiagnosticCode.UNSUPPORTED_NODE_TYPE: (
        FailureCategory.EXECUTION,
        "The failure record reports an unsupported node type. Review the runtime's supported components.",
    ),
    DiagnosticCode.INVALID_CONFIGURATION_VALUE: (
        FailureCategory.CONFIGURATION,
        "The failure record reports an invalid configuration value. Review the approved field constraints.",
    ),
    DiagnosticCode.AMBIGUOUS_INPUT_MAPPING: (
        FailureCategory.DATA_MAPPING,
        "The failure record reports an ambiguous input mapping. Confirm the intended source and destination.",
    ),
}
_NODE_SCOPED_CODES = _MISSING_CONFIGURATION_CODES | {
    DiagnosticCode.UNSUPPORTED_NODE_TYPE,
    DiagnosticCode.INVALID_CONFIGURATION_VALUE,
}


class RuleBasedDiagnoser:
    def __init__(
        self, definitions: Mapping[str, tuple[ConfigurationFieldDefinition, ...]]
    ) -> None:
        self._definitions = dict(definitions)

    def diagnose(
        self,
        failure: FailureInformation,
        requirements: OriginalRequirements,
        *,
        context: DiagnosisContext,
    ) -> DiagnosisResult:
        # These rules use structured evidence. Free-text requirements and logs may
        # contain private information or instructions and are never echoed.
        if (
            failure.workflow_id != context.workflow_id
            or failure.workflow_revision_id != context.workflow_revision_id
            or failure.execution_run_id != context.execution_run_id
        ):
            return _needs_analysis("The trusted context does not match the failed run and revision.")

        node = None
        if failure.failed_node_id is not None:
            matches = [node for node in context.nodes if node.node_id == failure.failed_node_id]
            if len(matches) != 1:
                return _needs_analysis("The reported node ID does not identify exactly one node in the revision.")
            node = matches[0]

        if context.configuration_evidence and (
            node is None or context.configuration_evidence.node_id != node.node_id
        ):
            return _needs_analysis("Configuration evidence does not match a confirmed failed node.")

        code = failure.error_code
        if node is None and code in _NODE_SCOPED_CODES:
            return _needs_analysis("This failure code requires a confirmed failed node ID.")

        if node is not None and code in _MISSING_CONFIGURATION_CODES:
            return self._diagnose_missing_configuration(
                node,
                context.configuration_evidence,
                instructions_only=code == DiagnosticCode.EMPTY_LLM_INSTRUCTIONS,
            )

        if classification := _MANUAL_CLASSIFICATIONS.get(code):
            category, explanation = classification
            return DiagnosisResult(
                category=category,
                affected_node_id=node.node_id if node else None,
                root_cause=explanation,
                supporting_evidence=("The reported structured code matched a manual-review rule.",),
                repairable=False,
                requires_human_intervention=True,
            )

        return _needs_analysis(
            "No deterministic rule matched the structured failure code.",
            node_id=node.node_id if node else None,
        )

    def _diagnose_missing_configuration(
        self,
        node: DiagnosticNode,
        evidence: ConfigurationEvidence | None,
        *,
        instructions_only: bool,
    ) -> DiagnosisResult:
        if evidence is None:
            return _needs_analysis("No trusted evidence identified a configuration field.", node_id=node.node_id)

        definitions = self._definitions.get(node.node_type, ())
        matches = [definition for definition in definitions if definition.name == evidence.field_name]
        if len(matches) != 1 or not matches[0].required:
            return _needs_analysis(
                "The reported field is not uniquely identified as required by the approved node schema.",
                node_id=node.node_id,
            )
        definition = matches[0]
        if instructions_only or definition.is_instruction_field:
            instruction_fields = [item for item in definitions if item.is_instruction_field]
            if instruction_fields != [definition]:
                return _needs_analysis(
                    "The approved node schema does not identify a single required instructions field.",
                    node_id=node.node_id,
                )

        value = node.configuration.get(definition.name)
        if not definition.is_missing(value):
            return _needs_analysis(
                "The approved field is present in the trusted revision. The missing-field report needs review.",
                node_id=node.node_id,
            )

        repairable = definition.allow_automatic_repair and evidence.has_trusted_replacement
        source_evidence = (
            "The field policy permits repair and the adapter confirmed an approved replacement source."
            if repairable
            else "A permitted repair with a trusted replacement source has not been established."
        )
        return DiagnosisResult(
            category=FailureCategory.CONFIGURATION,
            affected_node_id=node.node_id,
            affected_configuration_field=definition.name,
            root_cause=f"Required configuration field '{definition.name}' is missing or empty.",
            supporting_evidence=(
                "Trusted field evidence and the approved schema agree on the required field.",
                "The original revision contains no usable value for that field.",
                source_evidence,
            ),
            repairable=repairable,
            requires_human_intervention=not repairable,
        )


def _needs_analysis(reason: str, *, node_id: str | None = None) -> DiagnosisResult:
    return DiagnosisResult(
        category=FailureCategory.UNKNOWN,
        affected_node_id=node_id,
        root_cause=reason,
        repairable=False,
        requires_human_intervention=True,
    )
