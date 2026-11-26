from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.reliability import (
    CriticalDefectType,
    ExpectedHandling,
    FailureDiagnosticPayload,
    ReliabilityCategory,
    ScenarioResult,
    ScenarioStatus,
)

TransitionClassification = Literal[
    "FIXED",
    "UNRESOLVED",
    "STABLE",
    "REGRESSION",
    "INCOMPLETE",
    "NOT_RUN",
]

RegressionVerdict = Literal[
    "VERIFIED_SUCCESS",
    "PARTIAL_SUCCESS",
    "REGRESSION_DETECTED",
    "UNRESOLVED",
    "INCOMPLETE",
]


class BaselineScenarioEntry(BaseModel):
    """Pre-repair scenario result preserving original sample input and error context."""

    scenario_id: str
    category: ReliabilityCategory
    stress_vector: str = "GENERAL"
    sample_input: Dict[str, Any]
    expected_handling: ExpectedHandling
    status: ScenarioStatus
    actual_handling: Optional[str] = None
    critical_defect: Optional[CriticalDefectType] = None
    actual_output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    failing_node_id: Optional[str] = None
    failing_node_type: Optional[str] = None
    duration_ms: Optional[float] = None


class BaselineSnapshot(BaseModel):
    """Immutable pre-repair baseline snapshot for regression comparison."""

    workflow_id: str
    workflow_version: Optional[str] = None
    workflow_fingerprint: Optional[str] = None
    tested_at: datetime
    baseline_results: List[BaselineScenarioEntry] = Field(default_factory=list)


class ScenarioTransition(BaseModel):
    """Before-and-after outcome transition for a single scenario."""

    scenario_id: str
    category: ReliabilityCategory
    sample_input: Dict[str, Any]
    expected_handling: ExpectedHandling
    before_status: ScenarioStatus
    after_status: ScenarioStatus
    classification: TransitionClassification
    before_error: Optional[str] = None
    after_error: Optional[str] = None
    note: Optional[str] = None


class RegressionDiff(BaseModel):
    """Aggregated transition counts and scenario-level diffs."""

    total_scenarios: int = Field(..., ge=0)
    fixed_count: int = Field(..., ge=0)
    unresolved_count: int = Field(..., ge=0)
    stable_count: int = Field(..., ge=0)
    regression_count: int = Field(..., ge=0)
    incomplete_count: int = Field(..., ge=0)
    missing_post_repair_ids: List[str] = Field(default_factory=list)
    unexpected_post_repair_ids: List[str] = Field(default_factory=list)
    transitions: List[ScenarioTransition] = Field(default_factory=list)


class RegressionCompareRequest(BaseModel):
    """Request body for POST /api/v1/workflows/{workflow_id}/regression/compare."""

    baseline: BaselineSnapshot
    post_repair_results: List[ScenarioResult]
    post_repair_version: Optional[str] = None
    post_repair_fingerprint: Optional[str] = None


class RegressionReport(BaseModel):
    """Complete before-and-after regression verification report."""

    workflow_id: str
    pre_repair_version: Optional[str] = None
    pre_repair_fingerprint: Optional[str] = None
    post_repair_version: Optional[str] = None
    post_repair_fingerprint: Optional[str] = None
    generated_at: datetime
    total_scenarios: int = Field(..., ge=0)
    fixed_count: int = Field(..., ge=0)
    unresolved_count: int = Field(..., ge=0)
    stable_count: int = Field(..., ge=0)
    regression_count: int = Field(..., ge=0)
    incomplete_count: int = Field(..., ge=0)
    pre_repair_score: Optional[float] = None
    post_repair_score: Optional[float] = None
    delta_score: Optional[float] = None
    verdict: RegressionVerdict
    diff: RegressionDiff
    failure_diagnostics: List[FailureDiagnosticPayload] = Field(default_factory=list)
    summary: str
