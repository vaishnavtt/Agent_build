from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.validation import ValidationIssueDetail

TestCategory = Literal["normal", "invalid", "edge"]
TestStatus = Literal["NOT_RUN"]


class TestCaseSchema(BaseModel):
    """Structured representation of a single generated workflow test case."""

    test_case_id: str = Field(..., description="Unique identifier for the test case")
    name: str = Field(..., description="Short descriptive name of the test case")
    description: str = Field(..., description="Detailed explanation of what this test verifies")
    category: TestCategory = Field(..., description="Test category: normal, invalid, or edge")
    sample_input: Dict[str, Any] = Field(
        ..., description="Sample input payload structured for the workflow's Input node"
    )
    expected_behavior: str = Field(
        ..., description="Expected workflow behavior or outcome for this input"
    )
    status: TestStatus = Field(
        default="NOT_RUN",
        description="Execution status (always NOT_RUN upon generation)",
    )


class TestGenerationRequest(BaseModel):
    """Optional request body for automated test case generation."""

    requirement: Optional[str] = Field(
        default=None,
        description="Optional override for the original user requirement (defaults to workflow.description)",
    )
    categories: Optional[List[TestCategory]] = Field(
        default=None,
        description="Optional subset of test categories to generate (defaults to normal, invalid, edge)",
    )

    model_config = ConfigDict(json_schema_extra={"example": {}})


class TestGenerationResponse(BaseModel):
    """Response returned by POST /api/v1/workflows/{workflow_id}/tests/generate."""

    workflow_id: str
    workflow_name: str
    requirement_used: str
    input_type_detected: str
    input_required: bool
    validation_passed: bool
    validation_readiness_score: int = Field(..., ge=0, le=100)
    validation_warnings: List[ValidationIssueDetail] = Field(default_factory=list)
    total_tests: int = Field(..., ge=0)
    test_cases: List[TestCaseSchema] = Field(default_factory=list)
    note: str = Field(
        default="Test cases generated with status NOT_RUN. Execution requires Member 4's execution engine."
    )
