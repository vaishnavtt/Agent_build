from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.workflow_service import WorkflowService
from app.services.execution_service import ExecutionService
from app.schemas.workflow import WorkflowCreate, WorkflowRead
from app.schemas.execution import WorkflowExecuteRequest, ExecutionReportResponse
from app.engine.runner import execution_engine
from app.engine.types import ExecutionEngineError

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("", response_model=WorkflowRead, status_code=status.HTTP_201_CREATED)
def create_workflow(
    workflow_in: WorkflowCreate,
    db: Session = Depends(get_db),
):
    """Create and persist a new visual workflow graph."""
    service = WorkflowService(db)
    return service.create_workflow(workflow_in)


@router.get("", response_model=List[WorkflowRead])
def list_workflows(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """List active workflows with pagination."""
    service = WorkflowService(db)
    return service.list_workflows(skip=skip, limit=limit)


@router.get("/{workflow_id}", response_model=WorkflowRead)
def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve a single workflow definition by ID."""
    service = WorkflowService(db)
    workflow = service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )
    return workflow


@router.post("/{workflow_id}/execute", response_model=ExecutionReportResponse)
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    db: Session = Depends(get_db),
):
    """Execute a persisted visual workflow graph by its ID."""
    workflow_service = WorkflowService(db)
    exec_service = ExecutionService(db)

    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' does not exist.",
        )

    workflow_dict = {
        "id": workflow.id,
        "name": workflow.name,
        "version": workflow.version,
        "nodes": workflow.nodes,
        "edges": workflow.edges,
        "configuration": workflow.configuration,
    }

    import uuid
    execution_id = str(uuid.uuid4())
    exec_service.create_execution_record(
        execution_id=execution_id,
        workflow_id=workflow.id,
        input_payload=request.inputs,
    )

    try:
        report = await execution_engine.execute(
            workflow=workflow_dict,
            inputs=request.inputs,
            execution_id=execution_id,
        )
        ctx = execution_engine.get_context(execution_id)
        exec_service.update_execution_record(
            execution_id, report, context_dict=ctx.to_dict() if ctx else None
        )
        return report
    except ExecutionEngineError as ee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": ee.message, "node_id": ee.node_id, "stage": ee.stage},
        )
