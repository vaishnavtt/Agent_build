from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.workflow_service import WorkflowService
from app.schemas.workflow import WorkflowExecutionRead

router = APIRouter()


@router.get(
    "",
    response_model=List[WorkflowExecutionRead],
    status_code=status.HTTP_200_OK,
    summary="List All Executions",
    description="Retrieve execution history records across all workflows.",
)
def list_executions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[WorkflowExecutionRead]:
    service = WorkflowService(db)
    return service.list_executions(workflow_id=None, skip=skip, limit=limit)


@router.get(
    "/{execution_id}",
    response_model=WorkflowExecutionRead,
    status_code=status.HTTP_200_OK,
    summary="Get Execution Details",
    description="Retrieve detailed execution record by execution ID including logs and outputs.",
)
def get_execution_details(
    execution_id: str,
    db: Session = Depends(get_db),
) -> WorkflowExecutionRead:
    service = WorkflowService(db)
    exec_rec = service.get_execution(execution_id)
    if not exec_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution with ID '{execution_id}' not found.",
        )
    return exec_rec
