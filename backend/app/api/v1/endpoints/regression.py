import json
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.regression import RegressionCompareRequest, RegressionReport
from app.services.regression import (
    RegressionComparisonError,
    RegressionService,
    compute_workflow_fingerprint,
)
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
    "/{workflow_id}/regression/compare",
    response_model=RegressionReport,
    status_code=status.HTTP_200_OK,
    summary="Compare Pre-Repair and Post-Repair Results",
    description=(
        "Compares a pre-repair BaselineSnapshot against genuine post-repair ScenarioResults "
        "to classify FIXED, UNRESOLVED, STABLE, REGRESSION, and INCOMPLETE transitions."
    ),
)
def compare_regression_results(
    workflow_id: str,
    payload: RegressionCompareRequest,
    db: Session = Depends(get_db),
) -> RegressionReport:
    service = WorkflowService(db)
    workflow = service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )

    nodes = _ensure_list(workflow.nodes)
    edges = _ensure_list(workflow.edges)

    post_version = payload.post_repair_version or workflow.version
    post_fingerprint = payload.post_repair_fingerprint or compute_workflow_fingerprint(nodes, edges)

    reg_service = RegressionService()
    try:
        return reg_service.compare_and_report(
            workflow_id=workflow_id,
            baseline=payload.baseline,
            post_repair_results=payload.post_repair_results,
            post_repair_version=post_version,
            post_repair_fingerprint=post_fingerprint,
        )
    except RegressionComparisonError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
