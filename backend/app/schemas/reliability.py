from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

ReliabilityCategory = Literal["normal", "robustness", "edge"]
ExpectedHandling = Literal["SUCCESS", "SAFE_REJECTION", "GRACEFUL_HANDLING"]
ScenarioStatus = Literal["NOT_RUN", "PASSED", "FAILED"]
CriticalDefectType = Literal["UNHANDLED_CRASH", "TIMEOUT_VIOLATION", "CORRUPTED_OUTPUT"]
FailureType = Literal[
    "UNCAUGHT_EXCEPTION",
    "TIMEOUT",
    "CORRUPTED_OUTPUT",
    "ROBUSTNESS_BREACH",
    "EXECUTION_FAILURE",
]


class ReliabilityScenario(BaseModel):
    """A single deterministic reliability test scenario."""

    scenario_id: str
    name: str
    description: str
    category: ReliabilityCategory
    stress_vector: str
    sample_input: Dict[str, Any]
    expected_handling: ExpectedHandling
    status: Literal["NOT_RUN"] = "NOT_RUN"


class ReliabilityScenarioGenerationResponse(BaseModel):
    """Response returned by POST /api/v1/workflows/{workflow_id}/reliability/scenarios."""

    workflow_id: str
    workflow_name: str
    input_type_detected: str
    input_required: bool
    validation_passed: bool
    validation_readiness_score: int = Field(..., ge=0, le=100)
    total_scenarios: int = Field(..., ge=0)
    scenarios_by_category: Dict[ReliabilityCategory, List[ReliabilityScenario]]
    note: str = Field(
        default=(
            "Reliability scenarios generated with status NOT_RUN. "
            "Execution requires Member 4's workflow execution engine."
        )
    )


class ScenarioResult(BaseModel):
    """Recorded outcome of a single reliability scenario."""

    scenario_id: str
    category: ReliabilityCategory
    stress_vector: str
    expected_handling: ExpectedHandling
    actual_handling: Optional[str] = None
    status: ScenarioStatus = "NOT_RUN"
    passed: Optional[bool] = None
    critical_defect: Optional[CriticalDefectType] = None
    actual_output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    failing_node_id: Optional[str] = None
    failing_node_type: Optional[str] = None
    duration_ms: Optional[float] = None


class CategoryScoreDetail(BaseModel):
    """Score and execution counts for a single reliability category."""

    completed: int = Field(..., ge=0)
    passed: int = Field(..., ge=0)
    failed: int = Field(..., ge=0)
    total: int = Field(..., ge=0)
    max_points: float = Field(..., ge=0)
    earned_points: Optional[float] = None


class ReliabilityScoreBreakdown(BaseModel):
    """Transparent breakdown of the deterministic reliability score."""

    normal: CategoryScoreDetail
    robustness: CategoryScoreDetail
    edge: CategoryScoreDetail
    unhandled_crashes: int = Field(default=0, ge=0)
    timeout_violations: int = Field(default=0, ge=0)
    corrupted_outputs: int = Field(default=0, ge=0)
    total_deductions: float = Field(default=0.0, ge=0.0)
    final_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    formula_description: str


class FailureDiagnosticPayload(BaseModel):
    """Standardized failure diagnostic contract for Member 6's self-repair module."""

    workflow_id: str
    scenario_id: str
    category: ReliabilityCategory
    stress_vector: str
    failure_type: FailureType
    failing_node_id: Optional[str] = None
    failing_node_type: Optional[str] = None
    input_payload: Dict[str, Any]
    expected_handling: ExpectedHandling
    actual_handling: Optional[str] = None
    actual_output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    timestamp: datetime


class ReliabilityReport(BaseModel):
    """Complete reliability evaluation report generated from scenario results."""

    workflow_id: str
    workflow_name: str
    generated_at: datetime
    total_scenarios: int = Field(..., ge=0)
    executed_scenarios: int = Field(..., ge=0)
    not_run_scenarios: int = Field(..., ge=0)
    passed_scenarios: int = Field(..., ge=0)
    failed_scenarios: int = Field(..., ge=0)
    reliability_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    score_breakdown: ReliabilityScoreBreakdown
    scenario_results: List[ScenarioResult] = Field(default_factory=list)
    failure_diagnostics: List[FailureDiagnosticPayload] = Field(default_factory=list)
    summary: str
