from typing import Dict, Any, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.execution_service import ExecutionService
from app.services.workflow_service import WorkflowService
from app.schemas.execution import (
    ExecutionReportResponse,
    NodeExecutionLog,
    ApprovalActionRequest,
)
from app.engine.runner import execution_engine
from app.engine.types import ExecutionContext, ExecutionEngineError

router = APIRouter(prefix="/executions", tags=["Executions"])


@router.post("/run", response_model=ExecutionReportResponse)
async def run_workflow_directly(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """Executes a workflow JSON payload directly without requiring prior database persistence."""
    workflow_data = payload.get("workflow", payload)
    inputs = payload.get("inputs", {})
    execution_id = str(uuid.uuid4())

    workflow_id = (
        workflow_data.get("id")
        or workflow_data.get("metadata", {}).get("id")
        or "ad-hoc"
    )

    exec_service = ExecutionService(db)
    exec_service.create_execution_record(
        execution_id=execution_id,
        workflow_id=str(workflow_id),
        input_payload=inputs,
    )

    try:
        report = await execution_engine.execute(
            workflow=workflow_data,
            inputs=inputs,
            execution_id=execution_id,
        )
        exec_service.update_execution_record(execution_id, report)
        return report
    except ExecutionEngineError as ee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": ee.message, "node_id": ee.node_id, "stage": ee.stage},
        )


@router.get("/{execution_id}", response_model=Dict[str, Any])
def get_execution(
    execution_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve full execution status, outputs, metrics, and failure information."""
    exec_service = ExecutionService(db)
    record = exec_service.get_execution(execution_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution record '{execution_id}' not found.",
        )

    return {
        "execution_id": record.id,
        "workflow_id": record.workflow_id,
        "status": record.status,
        "input_payload": record.input_payload,
        "output_result": record.output_result,
        "error_message": record.error_message,
        "failed_node_id": record.failed_node_id,
        "metrics": record.metrics,
        "started_at": record.started_at.isoformat() if record.started_at else None,
        "completed_at": record.completed_at.isoformat() if record.completed_at else None,
    }


@router.get("/{execution_id}/logs", response_model=List[NodeExecutionLog])
def get_execution_logs(
    execution_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve structured node-level execution trace logs."""
    exec_service = ExecutionService(db)
    record = exec_service.get_execution(execution_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution record '{execution_id}' not found.",
        )
    return [NodeExecutionLog(**item) for item in (record.logs or [])]


@router.post("/{execution_id}/approve", response_model=ExecutionReportResponse)
async def approve_execution(
    execution_id: str,
    request: ApprovalActionRequest,
    db: Session = Depends(get_db),
):
    """Approve a paused human approval step and resume workflow execution."""
    exec_service = ExecutionService(db)
    record = exec_service.get_execution(execution_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution record '{execution_id}' not found.",
        )

    if record.status != "WAITING_FOR_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Execution '{execution_id}' is in status '{record.status}', not awaiting approval.",
        )

    workflow_service = WorkflowService(db)
    workflow = workflow_service.get_workflow(record.workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{record.workflow_id}' not found.",
        )

    context_dict = record.execution_context
    if context_dict and isinstance(context_dict, dict) and "execution_id" in context_dict:
        context = ExecutionContext.from_dict(context_dict)
    else:
        cached_ctx = execution_engine.get_context(execution_id)
        if not cached_ctx:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Execution context for '{execution_id}' could not be resolved.",
            )
        context = cached_ctx

    workflow_dict = {
        "id": workflow.id,
        "name": workflow.name,
        "version": workflow.version,
        "nodes": workflow.nodes,
        "edges": workflow.edges,
        "configuration": workflow.configuration,
    }

    report = await execution_engine.resume_after_approval(
        workflow=workflow_dict,
        context=context,
        action="approve",
        comment=request.comment,
        data=request.data,
    )
    exec_service.update_execution_record(execution_id, report, context.to_dict())
    return report


@router.post("/{execution_id}/reject", response_model=ExecutionReportResponse)
async def reject_execution(
    execution_id: str,
    request: ApprovalActionRequest,
    db: Session = Depends(get_db),
):
    """Reject a paused human approval step and terminate execution."""
    exec_service = ExecutionService(db)
    record = exec_service.get_execution(execution_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution record '{execution_id}' not found.",
        )

    workflow_service = WorkflowService(db)
    workflow = workflow_service.get_workflow(record.workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{record.workflow_id}' not found.",
        )

    context_dict = record.execution_context
    if context_dict and isinstance(context_dict, dict) and "execution_id" in context_dict:
        context = ExecutionContext.from_dict(context_dict)
    else:
        cached_ctx = execution_engine.get_context(execution_id)
        if not cached_ctx:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Execution context for '{execution_id}' could not be resolved.",
            )
        context = cached_ctx

    workflow_dict = {
        "id": workflow.id,
        "name": workflow.name,
        "version": workflow.version,
        "nodes": workflow.nodes,
        "edges": workflow.edges,
        "configuration": workflow.configuration,
    }

    report = await execution_engine.resume_after_approval(
        workflow=workflow_dict,
        context=context,
        action="reject",
        comment=request.comment or "Approval denied",
        data=request.data,
    )
    exec_service.update_execution_record(execution_id, report, context.to_dict())
    return report
