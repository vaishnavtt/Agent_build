import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.validation import FullWorkflowValidateRequest, FullWorkflowValidationResponse
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
    "/{workflow_id}/validate-full",
    response_model=FullWorkflowValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Full Workflow Validation",
    description=(
        "Performs comprehensive structural, configuration, connection, handle, "
        "and I/O validation with a deterministic readiness score. "
        "Omit the request body or send `{}` to validate the persisted SQLite workflow."
    ),
)
def validate_workflow_full(
    workflow_id: str,
    payload: Optional[FullWorkflowValidateRequest] = Body(default=None),
    db: Session = Depends(get_db),
) -> FullWorkflowValidationResponse:
    service = WorkflowService(db)
    workflow = service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )

    nodes = (
        payload.nodes
        if payload is not None and payload.nodes is not None
        else _ensure_list(workflow.nodes)
    )
    edges = (
        payload.edges
        if payload is not None and payload.edges is not None
        else _ensure_list(workflow.edges)
    )

    validator = WorkflowValidator()
    return validator.validate(nodes=nodes, edges=edges, workflow_id=workflow_id)
