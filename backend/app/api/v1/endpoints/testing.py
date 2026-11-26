import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.testing import TestGenerationRequest, TestGenerationResponse
from app.services.testing import TestCaseGenerator
from app.services.validation import WorkflowValidator
from app.services.workflow_service import WorkflowService

router = APIRouter()


def _ensure_list(value: Any) -> List[Dict[str, Any]]:
    """Ensure persisted JSON column values are returned as a list of dicts."""
    if value is None:
        return []
    if isinstance(value, str):
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    if isinstance(value, list):
        return value
    return []


@router.post(
    "/{workflow_id}/tests/generate",
    response_model=TestGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Automated Test Cases",
    description=(
        "Generates Normal, Invalid, and Edge-case test cases for a persisted workflow "
        "after pre-flight validation. Generated cases have initial status NOT_RUN."
    ),
)
def generate_workflow_tests(
    workflow_id: str,
    payload: Optional[TestGenerationRequest] = Body(default=None),
    db: Session = Depends(get_db),
) -> TestGenerationResponse:
    service = WorkflowService(db)
    workflow = service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )

    nodes = _ensure_list(workflow.nodes)
    edges = _ensure_list(workflow.edges)

    # Pre-flight validation using Stage 1 WorkflowValidator
    validator = WorkflowValidator()
    validation_result = validator.validate(nodes=nodes, edges=edges, workflow_id=workflow_id)

    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Workflow failed pre-flight validation. Fix validation errors before generating test cases.",
                "workflow_id": workflow_id,
                "readiness_score": validation_result.readiness_score,
                "validation_errors": [e.model_dump() for e in validation_result.errors],
            },
        )

    requirement_override = payload.requirement if payload is not None else None
    effective_requirement = (
        requirement_override
        if isinstance(requirement_override, str) and requirement_override.strip()
        else workflow.description
    )
    categories = payload.categories if payload is not None else None

    generator = TestCaseGenerator()
    test_cases, requirement_used, input_type, input_required = generator.generate(
        nodes=nodes,
        edges=edges,
        requirement=effective_requirement,
        workflow_name=workflow.name,
        categories=categories,
    )

    return TestGenerationResponse(
        workflow_id=workflow_id,
        workflow_name=workflow.name,
        requirement_used=requirement_used,
        input_type_detected=input_type,
        input_required=input_required,
        validation_passed=True,
        validation_readiness_score=validation_result.readiness_score,
        validation_warnings=validation_result.warnings,
        total_tests=len(test_cases),
        test_cases=test_cases,
    )
