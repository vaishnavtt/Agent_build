"""Pydantic schemas for Member 2: AI Requirement Analysis & Agent Architect Module.

Provides stable data models and contract definitions for:
- Natural-language requirement analysis request & response
- Requirements breakdown (inputs, processing, outputs, tools, constraints)
- Ordered task decomposition with dependencies
- Supported canonical component validation
- Requirement clarification questions
- Structured execution plan passed to Member 3 (Workflow Generation Module)
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, model_validator


# Supported Canonical Components in AgentForge AI
SupportedComponent = Literal[
    "Input",
    "LLM",
    "Document Reader",
    "Tool",
    "Condition",
    "Human Approval",
    "Output",
]

SUPPORTED_COMPONENTS_LIST: List[SupportedComponent] = [
    "Input",
    "LLM",
    "Document Reader",
    "Tool",
    "Condition",
    "Human Approval",
    "Output",
]


class TaskDecompositionItem(BaseModel):
    """An ordered, executable task decomposed from requirements."""

    task_id: str = Field(..., description="Unique task identifier, e.g. T1, T2")
    task_name: str = Field(..., description="Concise human-readable task name")
    description: str = Field(default="", description="Detailed explanation of what the task performs")
    task_description: str = Field(default="", description="Alias for description for backward/forward compatibility")
    component: SupportedComponent = Field(..., description="Required canonical workflow component")
    component_type: Optional[SupportedComponent] = Field(
        default=None,
        description="Alias for component matching Member 2 task decomposition specification"
    )
    required_component: Optional[SupportedComponent] = Field(
        default=None,
        description="Alias for component for contract compatibility"
    )
    input: str = Field(default="", description="Inputs consumed by this task")
    expected_output: str = Field(default="", description="Output produced by this task")
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of prerequisite task IDs that must complete before this task executes"
    )
    execution_order: int = Field(..., ge=1, description="1-based topological execution sequence order")
    component_config_hints: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Configuration parameters and hints for Member 3's node configuration"
    )

    @model_validator(mode="after")
    def sync_aliases(self):
        # Sync description and task_description
        if not self.description and self.task_description:
            self.description = self.task_description
        elif not self.task_description and self.description:
            self.task_description = self.description

        # Sync component, component_type, and required_component
        chosen_comp = self.component or self.component_type or self.required_component
        self.component = chosen_comp
        self.component_type = chosen_comp
        self.required_component = chosen_comp
        return self


class RequirementsBreakdown(BaseModel):
    """Extracted requirements categorized by purpose."""

    functional: List[str] = Field(default_factory=list, description="Functional capabilities and business logic")
    non_functional: List[str] = Field(default_factory=list, description="Non-functional requirements like latency, safety, scalability")
    inputs: List[str] = Field(default_factory=list, description="Data and trigger inputs required")
    processing: List[str] = Field(default_factory=list, description="Processing and reasoning steps needed")
    outputs: List[str] = Field(default_factory=list, description="Expected artifacts, reports, or results")
    expected_outputs: List[str] = Field(default_factory=list, description="Alias for outputs for schema flexibility")
    tools: List[str] = Field(default_factory=list, description="External tools, APIs, or data integrations")
    constraints: List[str] = Field(default_factory=list, description="Constraints, timeouts, or policy rules")

    @model_validator(mode="after")
    def sync_outputs(self):
        if not self.outputs and self.expected_outputs:
            self.outputs = list(self.expected_outputs)
        elif not self.expected_outputs and self.outputs:
            self.expected_outputs = list(self.outputs)
        return self


class AcceptanceCriterion(BaseModel):
    """Measurable, testable acceptance criterion for verifying workflow fulfillment."""

    id: str = Field(..., description="Unique criterion identifier e.g. AC1, AC2")
    requirement_id: Optional[str] = Field(default=None, description="Linked requirement ID e.g. REQ-1 or FR1")
    criteria: str = Field(..., description="Specific, verifiable rule or condition to satisfy")
    description: Optional[str] = Field(default="", description="Detailed explanation of the criterion")
    pass_condition: Optional[str] = Field(default=None, description="Explicit testable pass condition")


class EdgeCaseScenario(BaseModel):
    """Edge-case or invalid-input failure scenario to ensure workflow resilience."""

    scenario_id: str = Field(..., description="Unique scenario ID e.g. EC1, EC2")
    description: str = Field(..., description="Description of the edge case or failure mode")
    input_condition: str = Field(..., description="Specific abnormal, boundary, or invalid input triggering the scenario")
    expected_behavior: str = Field(..., description="Expected system handling (e.g. graceful error, fallback, human alert)")
    expected_result: Optional[str] = Field(default="", description="Expected outcome or error response")
    severity: Literal["Low", "Medium", "High", "Critical"] = Field(
        default="Medium",
        description="Severity level of the edge case impact"
    )


class TestScenario(BaseModel):
    """Automated test scenario for Member 5 testing module and validation."""

    test_id: str = Field(..., description="Unique test scenario ID e.g. TS1, TS2")
    requirement_id: Optional[str] = Field(default=None, description="Linked requirement or acceptance criterion ID")
    test_description: str = Field(..., description="Description of test purpose")
    test_input: Any = Field(default="", description="Sample test input payload or parameters")
    expected_output: Any = Field(default="", description="Expected output or response payload")
    expected_status: str = Field(default="SUCCESS", description="Expected execution status e.g. SUCCESS, FAILURE, ERROR")
    pass_fail_condition: str = Field(..., description="Measurable evaluation check to determine pass/fail")
    scenario_type: Literal["positive", "negative", "edge_case"] = Field(
        default="positive",
        description="Scenario type for test stratification"
    )


class ClarificationQuestion(BaseModel):
    """Clarification question generated when requirements are ambiguous or missing."""

    id: str = Field(..., description="Identifier for question, e.g. Q1, Q2")
    question: str = Field(..., description="The clarification question for the user")
    reason: str = Field(..., description="Explanation of why clarification is needed to build a reliable plan")
    category: Optional[str] = Field(default="clarification", description="Question category e.g. input, criteria, output")


class AnalysisRequest(BaseModel):
    """User input for AI requirement analysis."""

    description: str = Field(
        ...,
        min_length=3,
        description="User's natural-language agent description"
    )
    clarification_answers: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Key-value mapping of clarification question IDs to user answers"
    )
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional additional context or user preferences"
    )


class ExecutionPlanResponse(BaseModel):
    """Structured execution plan output, ready for handoff to Member 3 (Workflow Generation)."""

    project_objective: str = Field(..., description="Understood high-level objective of the agent")
    status: Literal["ready", "needs_clarification"] = Field(
        default="ready",
        description="Status of planning: ready for workflow generation or needs user clarification"
    )
    requirements: RequirementsBreakdown = Field(
        default_factory=RequirementsBreakdown,
        description="Structured extracted requirements"
    )
    tasks: List[TaskDecompositionItem] = Field(
        default_factory=list,
        description="Ordered executable task decomposition"
    )
    execution_plan: Optional[List[TaskDecompositionItem]] = Field(
        default=None,
        description="Alias for tasks for Member 3 / Member 5 execution plan format"
    )
    required_components: List[SupportedComponent] = Field(
        default_factory=list,
        description="Deduplicated list of required canonical components"
    )
    components: Optional[List[SupportedComponent]] = Field(
        default=None,
        description="Alias for required_components"
    )
    clarification_questions: List[ClarificationQuestion] = Field(
        default_factory=list,
        description="Questions to ask user if requirements are incomplete or ambiguous"
    )
    acceptance_criteria: List[AcceptanceCriterion] = Field(
        default_factory=list,
        description="Testable acceptance criteria for Member 5 testing & repair verification"
    )
    edge_cases: List[EdgeCaseScenario] = Field(
        default_factory=list,
        description="Identified edge cases and invalid-input handling scenarios"
    )
    test_scenarios: List[TestScenario] = Field(
        default_factory=list,
        description="Generated test scenarios for Member 5 automated testing module"
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Technical and operational assumptions made during architecture synthesis"
    )
    confidence_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score in the requirement analysis and plan completeness"
    )
    architecture_summary: Optional[str] = Field(
        default=None,
        description="Short technical architecture summary of the designed agent workflow"
    )
    ai_provider: Literal["google-gemini", "deterministic_engine", "mock"] = Field(
        default="deterministic_engine",
        description="Transparent indicator of whether Gemini API or deterministic fallback generated the analysis"
    )
    model_used: Optional[str] = Field(
        default=None,
        description="Name of the Gemini model used (e.g. gemini-1.5-pro) or engine name"
    )
    contract_version: str = Field(
        default="1.1.0",
        description="Contract schema version for Member 3 and Member 5 compatibility"
    )

    @model_validator(mode="after")
    def sync_aliases(self):
        # Sync tasks and execution_plan
        if not self.execution_plan and self.tasks:
            self.execution_plan = list(self.tasks)
        elif not self.tasks and self.execution_plan:
            self.tasks = list(self.execution_plan)

        # Sync required_components and components
        if not self.components and self.required_components:
            self.components = list(self.required_components)
        elif not self.required_components and self.components:
            self.required_components = list(self.components)

        return self
