"""Deterministic-first diagnosis with an advisory-only Gemini fallback."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from pydantic import ValidationError

from app.schemas.repair import DiagnosisResult, FailureCategory, FailureInformation
from app.services.repair.diagnosis import (
    ConfigurationFieldDefinition,
    DiagnosisContext,
    ExternalDiagnosticFact,
    OriginalRequirements,
    RuleBasedDiagnoser,
)
from app.services.repair.gemini_diagnosis import (
    ComplexFailureCode,
    DiagnosticAction,
    GeminiDiagnosticContext,
    GeminiHypothesis,
    GeminiProvider,
    ProviderIssue,
    ProviderUsage,
    SuspectedCause,
)


class DiagnosisStatus(StrEnum):
    DETERMINISTIC = "deterministic"
    UNRESOLVED = "unresolved"
    ADVISORY = "advisory"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    RESPONSE_REJECTED = "response_rejected"


@dataclass(frozen=True)
class DiagnosisOutcome:
    deterministic: DiagnosisResult
    status: DiagnosisStatus
    advisory: DiagnosisResult | None = None
    hypothesis: GeminiHypothesis | None = None
    provider_issue: ProviderIssue | None = None
    usage: ProviderUsage = field(default_factory=ProviderUsage)

    @property
    def diagnosis(self) -> DiagnosisResult:
        return self.advisory or self.deterministic


_REQUIRED_FACT = {
    ComplexFailureCode.UNEXPECTED_OUTPUT_SHAPE: ExternalDiagnosticFact.OUTPUT_SHAPE_MISMATCH,
    ComplexFailureCode.NODE_EXECUTION_ERROR: ExternalDiagnosticFact.NODE_EXECUTION_HALTED,
    ComplexFailureCode.TEST_ASSERTION_MISMATCH: ExternalDiagnosticFact.TEST_ASSERTION_MISMATCH,
}
_FALLBACK_NODE_TYPES = {"Input", "LLM", "Document Reader", "Condition", "Output"}
_MAX_RESPONSE_LENGTH = 4096


@dataclass(frozen=True)
class _HypothesisPolicy:
    category: FailureCategory
    action: DiagnosticAction
    required_fact: ExternalDiagnosticFact | None
    explanation: str


_HYPOTHESIS_POLICIES = {
    SuspectedCause.OUTPUT_CONTRACT_MISMATCH: _HypothesisPolicy(
        FailureCategory.EXECUTION, DiagnosticAction.REVIEW_OUTPUT_CONTRACT,
        ExternalDiagnosticFact.OUTPUT_SHAPE_MISMATCH,
        "The node may be producing a result that differs from its output contract. Review the expected shape.",
    ),
    SuspectedCause.UPSTREAM_DATA_SHAPE_MISMATCH: _HypothesisPolicy(
        FailureCategory.DATA_MAPPING, DiagnosticAction.REVIEW_UPSTREAM_SHAPE,
        ExternalDiagnosticFact.UPSTREAM_OUTPUT_PRESENT,
        "Upstream output may have an unexpected shape. Review the original input and output contracts.",
    ),
    SuspectedCause.NODE_RUNTIME_FAILURE: _HypothesisPolicy(
        FailureCategory.EXECUTION, DiagnosticAction.REVIEW_NODE_EXECUTION,
        ExternalDiagnosticFact.NODE_EXECUTION_HALTED,
        "A runtime failure may have interrupted the node. Inspect the retained execution evidence locally.",
    ),
    SuspectedCause.TEST_EXPECTATION_MISMATCH: _HypothesisPolicy(
        FailureCategory.TEST_ASSERTION, DiagnosticAction.REVIEW_ORIGINAL_ASSERTIONS,
        ExternalDiagnosticFact.TEST_ASSERTION_MISMATCH,
        "The observed result may differ from an original test expectation. Review the existing assertion.",
    ),
    SuspectedCause.CONFIGURATION_CONTRACT_MISMATCH: _HypothesisPolicy(
        FailureCategory.CONFIGURATION, DiagnosticAction.REVIEW_APPROVED_SETTING,
        ExternalDiagnosticFact.OUTPUT_SHAPE_MISMATCH,
        "An approved setting may be related to the output mismatch. Review the setting locally.",
    ),
    SuspectedCause.INSUFFICIENT_EVIDENCE: _HypothesisPolicy(
        FailureCategory.UNKNOWN, DiagnosticAction.COLLECT_MORE_EVIDENCE, None, "",
    ),
}


class DiagnosisRouter:
    def __init__(
        self,
        definitions: Mapping[str, tuple[ConfigurationFieldDefinition, ...]],
        provider: GeminiProvider,
    ) -> None:
        self._definitions = {node_type: tuple(items) for node_type, items in definitions.items()}
        self._deterministic = RuleBasedDiagnoser(self._definitions)
        self._provider = provider

    def diagnose(
        self, failure: FailureInformation, requirements: OriginalRequirements, *, context: DiagnosisContext
    ) -> DiagnosisResult:
        """Keep the existing FailureDiagnoser interface for callers without telemetry."""
        return self.diagnose_with_details(failure, requirements, context=context).diagnosis

    def diagnose_with_details(
        self, failure: FailureInformation, requirements: OriginalRequirements, *, context: DiagnosisContext
    ) -> DiagnosisOutcome:
        deterministic = self._deterministic.diagnose(failure, requirements, context=context)
        if deterministic.category != FailureCategory.UNKNOWN:
            return DiagnosisOutcome(deterministic, DiagnosisStatus.DETERMINISTIC)

        request = self._eligible_context(failure, context, deterministic)
        if request is None:
            return DiagnosisOutcome(deterministic, DiagnosisStatus.UNRESOLVED)

        try:
            reply = self._provider.generate(request)
        except Exception:
            return DiagnosisOutcome(
                deterministic, DiagnosisStatus.PROVIDER_UNAVAILABLE,
                provider_issue=ProviderIssue.PROVIDER_UNAVAILABLE, usage=ProviderUsage(calls=None),
            )
        if reply.issue is not None:
            status = (
                DiagnosisStatus.RESPONSE_REJECTED
                if reply.issue in (ProviderIssue.EMPTY_RESPONSE, ProviderIssue.INVALID_RESPONSE)
                else DiagnosisStatus.PROVIDER_UNAVAILABLE
            )
            return DiagnosisOutcome(deterministic, status, provider_issue=reply.issue, usage=reply.usage)
        if not reply.text or not reply.text.strip():
            return DiagnosisOutcome(
                deterministic, DiagnosisStatus.RESPONSE_REJECTED,
                provider_issue=ProviderIssue.EMPTY_RESPONSE, usage=reply.usage,
            )

        hypothesis = _parse_hypothesis(reply.text, request)
        if hypothesis is None:
            return DiagnosisOutcome(
                deterministic, DiagnosisStatus.RESPONSE_REJECTED,
                provider_issue=ProviderIssue.INVALID_RESPONSE, usage=reply.usage,
            )
        if hypothesis.suspected_cause == SuspectedCause.INSUFFICIENT_EVIDENCE:
            return DiagnosisOutcome(deterministic, DiagnosisStatus.UNRESOLVED, usage=reply.usage)

        policy = _HYPOTHESIS_POLICIES[hypothesis.suspected_cause]
        advisory = DiagnosisResult(
            category=hypothesis.category,
            affected_node_id=deterministic.affected_node_id,
            affected_configuration_field=hypothesis.affected_field,
            root_cause=f"Gemini hypothesis: {policy.explanation}",
            supporting_evidence=tuple(f"Trusted observation: {fact.value}." for fact in hypothesis.evidence_refs),
            repairable=False,
            requires_human_intervention=True,
        )
        return DiagnosisOutcome(deterministic, DiagnosisStatus.ADVISORY, advisory, hypothesis, usage=reply.usage)

    def _eligible_context(
        self, failure: FailureInformation, context: DiagnosisContext, deterministic: DiagnosisResult
    ) -> GeminiDiagnosticContext | None:
        required_fact = _REQUIRED_FACT.get(failure.error_code)
        external = context.external_evidence
        if (
            required_fact is None
            or external is None
            or external.cleared_for_external_diagnosis is not True
            or failure.workflow_id != context.workflow_id
            or failure.workflow_revision_id != context.workflow_revision_id
            or failure.execution_run_id != context.execution_run_id
            or failure.failed_node_id is None
            or deterministic.affected_node_id != failure.failed_node_id
        ):
            return None
        allowed_facts = {required_fact, ExternalDiagnosticFact.UPSTREAM_OUTPUT_PRESENT}
        if (
            required_fact not in external.facts
            or not all(isinstance(fact, ExternalDiagnosticFact) and fact in allowed_facts for fact in external.facts)
            or len(set(external.facts)) != len(external.facts)
        ):
            return None

        nodes = [node for node in context.nodes if node.node_id == failure.failed_node_id]
        if len(nodes) != 1 or nodes[0].node_type not in _FALLBACK_NODE_TYPES:
            return None
        node = nodes[0]
        evidence = context.configuration_evidence
        approved_field = None
        if evidence is not None:
            definitions = self._definitions.get(node.node_type, ())
            approved = [item for item in definitions if item.name == evidence.field_name]
            if (
                evidence.node_id != node.node_id
                or len(approved) != 1
                or not approved[0].allow_external_diagnosis
                or (approved[0].is_instruction_field and sum(item.is_instruction_field for item in definitions) != 1)
            ):
                return None
            approved_field = approved[0].name
        try:
            return GeminiDiagnosticContext(
                node_type=node.node_type, error_code=failure.error_code,
                facts=external.facts, approved_field=approved_field,
            )
        except ValidationError:
            return None


def _parse_hypothesis(text: str, request: GeminiDiagnosticContext) -> GeminiHypothesis | None:
    if len(text) > _MAX_RESPONSE_LENGTH:
        return None
    try:
        hypothesis = GeminiHypothesis.model_validate_json(text, strict=True)
    except ValidationError:
        return None
    referenced = set(hypothesis.evidence_refs)
    policy = _HYPOTHESIS_POLICIES[hypothesis.suspected_cause]
    if (
        len(referenced) != len(hypothesis.evidence_refs)
        or not referenced.issubset(request.facts)
        or hypothesis.category != policy.category
        or hypothesis.suggested_action != policy.action
        or (policy.required_fact is not None and policy.required_fact not in referenced)
    ):
        return None
    if hypothesis.affected_field is not None and (
        hypothesis.affected_node_ref != request.node_ref or hypothesis.affected_field != request.approved_field
    ):
        return None
    if hypothesis.suspected_cause == SuspectedCause.CONFIGURATION_CONTRACT_MISMATCH and hypothesis.affected_field is None:
        return None
    return hypothesis
