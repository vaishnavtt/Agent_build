from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class FullWorkflowValidateRequest(BaseModel):
    """Optional request body for direct-payload validation.

    Omit the body or send `{}` to validate the workflow persisted in SQLite.
    """

    nodes: Optional[List[Dict[str, Any]]] = Field(default=None)
    edges: Optional[List[Dict[str, Any]]] = Field(default=None)

    model_config = ConfigDict(json_schema_extra={"example": {}})


class ValidationIssueDetail(BaseModel):
    """Structured representation of a single workflow validation error or warning."""

    issue_type: str = Field(..., description="Machine-readable validation issue code")
    severity: Literal["error", "warning"] = Field(..., description="Severity level")
    message: str = Field(..., description="Human-readable explanation of the issue")
    affected_node_id: Optional[str] = Field(
        default=None, description="ID of the node affected by this issue, if applicable"
    )
    affected_connection_id: Optional[str] = Field(
        default=None, description="ID of the edge/connection affected by this issue, if applicable"
    )


class ScoreBreakdown(BaseModel):
    """Transparent, deterministic breakdown of the workflow readiness score."""

    structural_score: int = Field(..., ge=0, le=30, description="Max 30 points for graph structure")
    connection_score: int = Field(..., ge=0, le=30, description="Max 30 points for valid connections & I/O")
    configuration_score: int = Field(..., ge=0, le=40, description="Max 40 points for node configurations")
    formula_description: str = Field(
        ...,
        description="Explanation of how the deterministic readiness score is calculated",
    )


class ValidationDetails(BaseModel):
    """Detailed structural, connectivity, and scoring diagnostics."""

    disconnected_node_ids: List[str] = Field(default_factory=list)
    unreachable_node_ids: List[str] = Field(default_factory=list)
    unsupported_node_ids: List[str] = Field(default_factory=list)
    invalid_connection_ids: List[str] = Field(default_factory=list)
    has_input_node: bool = False
    has_output_node: bool = False
    has_path_to_output: bool = False
    score_breakdown: ScoreBreakdown


class FullWorkflowValidationResponse(BaseModel):
    """Complete validation report returned by /api/v1/workflows/{workflow_id}/validate-full."""

    workflow_id: Optional[str] = None
    is_valid: bool
    readiness_score: int = Field(..., ge=0, le=100)
    total_nodes: int = Field(..., ge=0)
    total_connections: int = Field(..., ge=0)
    errors: List[ValidationIssueDetail] = Field(default_factory=list)
    warnings: List[ValidationIssueDetail] = Field(default_factory=list)
    validation_details: ValidationDetails
