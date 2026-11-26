import json
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.reliability import ReliabilityScenarioGenerationResponse
from app.services.reliability import ReliabilityLabService
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
    "/{workflow_id}/reliability/scenarios",
    response_model=ReliabilityScenarioGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Workflow Reliability Scenarios",
    description=(
        "Performs pre-flight validation on a saved workflow and generates Normal, "
        "Robustness, and Edge reliability scenarios with initial status NOT_RUN."
    ),
)
def generate_reliability_scenarios(
    workflow_id: str,
    db: Session = Depends(get_db),
) -> ReliabilityScenarioGenerationResponse:
    service = WorkflowService(db)
    workflow = service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )

    nodes = _ensure_list(workflow.nodes)
    edges = _ensure_list(workflow.edges)

    validator = WorkflowValidator()
    validation_result = validator.validate(nodes=nodes, edges=edges, workflow_id=workflow_id)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Workflow failed pre-flight validation. Fix validation errors before generating reliability scenarios.",
                "workflow_id": workflow_id,
                "readiness_score": validation_result.readiness_score,
                "validation_errors": [e.model_dump() for e in validation_result.errors],
            },
        )

    lab = ReliabilityLabService()
    grouped, input_type, input_required = lab.generate_scenarios(
        nodes=nodes,
        edges=edges,
        requirement=workflow.description,
        workflow_name=workflow.name,
    )

    total_scenarios = sum(len(items) for items in grouped.values())

    return ReliabilityScenarioGenerationResponse(
        workflow_id=workflow_id,
        workflow_name=workflow.name,
        input_type_detected=input_type,
        input_required=input_required,
        validation_passed=True,
        validation_readiness_score=validation_result.readiness_score,
        total_scenarios=total_scenarios,
        scenarios_by_category=grouped,
    )
