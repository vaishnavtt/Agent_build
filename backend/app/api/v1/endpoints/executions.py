from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.workflow_service import WorkflowService
from app.schemas.workflow import (
    WorkflowExecutionRead,
    WorkflowExecutionUpdate,
)
from app.core.security import get_current_principal, HostPrincipal, authorize_workflow_owner

router = APIRouter()


@router.get(
    "/{execution_id}",
    response_model=WorkflowExecutionRead,
    status_code=status.HTTP_200_OK,
    summary="Get Execution Record",
    description="Retrieve a specific workflow execution record by its unique execution ID.",
)
def get_execution(
    execution_id: str,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowExecutionRead:
    service = WorkflowService(db)
    record = service.get_execution(execution_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution record with ID '{execution_id}' not found.",
        )
    if record.workflow:
        authorize_workflow_owner(record.workflow, principal)
    return record


@router.patch(
    "/{execution_id}",
    response_model=WorkflowExecutionRead,
    status_code=status.HTTP_200_OK,
    summary="Update Execution Record",
    description="Update runtime execution telemetry, status transition, output payload, or error logs.",
)
def update_execution(
    execution_id: str,
    execution_in: WorkflowExecutionUpdate,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowExecutionRead:
    service = WorkflowService(db)
    record = service.get_execution(execution_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution record with ID '{execution_id}' not found.",
        )
    if record.workflow:
        authorize_workflow_owner(record.workflow, principal)

    updated = service.update_execution(execution_id, execution_in)
    return updated


@router.get(
    "",
    response_model=List[WorkflowExecutionRead],
    status_code=status.HTTP_200_OK,
    summary="List All Executions",
    description="Retrieve execution history records across all workflows with pagination and case-insensitive status filters.",
)
def list_all_executions(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    revision_id: Optional[str] = Query(None, description="Filter by revision ID"),
    status: Optional[str] = Query(None, description="Filter by execution status (case-insensitive)"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> List[WorkflowExecutionRead]:
    service = WorkflowService(db)
    return service.list_executions(
        workflow_id=workflow_id,
        revision_id=revision_id,
        skip=skip,
        limit=limit,
        status=status,
    )
