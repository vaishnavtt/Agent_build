from typing import Dict, Any, List, Optional
import uuid
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.session import get_db
from app.services.execution_service import ExecutionService, compute_workflow_revision_id
from app.services.workflow_service import WorkflowService
from app.schemas.execution import (
    ExecutionReportResponse,
    ExecutionStatus,
    NodeExecutionLog,
    ApprovalActionRequest,
)
from app.engine.runner import execution_engine
from app.engine.security import redact_sensitive_data
from app.engine.types import ExecutionContext, ExecutionEngineError

router = APIRouter(prefix="/executions", tags=["Executions"])


def _resolve_actor(
    x_user_id: Optional[str],
    authorization: Optional[str],
) -> Optional[str]:
    actor = (x_user_id or "").strip()
    if not actor and authorization and authorization.lower().startswith("bearer "):
        actor = authorization[7:].strip()[:64]
    if settings.ENVIRONMENT.lower() == "production" and not actor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required in production.",
        )
    return actor or None


def _check_execution_ownership(record: Any, actor: Optional[str]) -> None:
    if record.owner_id:
        if not actor or (actor != record.owner_id and actor != "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you do not own this execution record.",
            )


def _resolve_workflow_snapshot(record: Any, db: Session) -> Dict[str, Any]:
    """Resolves the exact immutable workflow snapshot for an execution (supports ad-hoc & saved)."""
    if record.workflow_snapshot and isinstance(record.workflow_snapshot, dict):
        return record.workflow_snapshot

    workflow_service = WorkflowService(db)
    workflow = workflow_service.get_workflow(record.workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{record.workflow_id}' snapshot not found.",
        )
    return {
        "id": workflow.id,
        "name": workflow.name,
        "version": workflow.version,
        "nodes": workflow.nodes,
        "edges": workflow.edges,
        "configuration": workflow.configuration,
    }


def _resolve_execution_context(record: Any) -> ExecutionContext:
    context_dict = record.execution_context
    if context_dict and isinstance(context_dict, dict) and "execution_id" in context_dict:
        return ExecutionContext.from_dict(context_dict)
    cached_ctx = execution_engine.get_context(record.id)
    if cached_ctx:
        return cached_ctx
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Execution context for '{record.id}' could not be resolved.",
    )


@router.get("", response_model=List[Dict[str, Any]])
def list_executions(
    workflow_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    """List non-candidate executions scoped to the authenticated actor when present."""
    actor = _resolve_actor(x_user_id, authorization)
    exec_service = ExecutionService(db)
    records = exec_service.list_executions(
        workflow_id=workflow_id,
        owner_id=actor if actor and actor != "admin" else None,
        include_candidates=False,
        skip=skip,
        limit=limit,
    )
    return [
        {
            "execution_id": r.id,
            "workflow_id": r.workflow_id,
            "workflow_revision_id": r.workflow_revision_id,
            "status": r.status,
            "error_message": r.error_message,
            "failed_node_id": r.failed_node_id,
            "metrics": r.metrics,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in records
    ]


@router.post("/run", response_model=ExecutionReportResponse)
async def run_workflow_directly(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    """Executes a workflow JSON payload directly without requiring prior database persistence."""
    actor = _resolve_actor(x_user_id, authorization)
    workflow_data = payload.get("workflow", payload)
    inputs = payload.get("inputs", {})
    execution_id = str(uuid.uuid4())

    workflow_id = (
        workflow_data.get("id")
        or workflow_data.get("metadata", {}).get("id")
        or "ad-hoc"
    )
    revision_id = compute_workflow_revision_id(workflow_data)

    exec_service = ExecutionService(db)
    exec_service.create_execution_record(
        execution_id=execution_id,
        workflow_id=str(workflow_id),
        input_payload=redact_sensitive_data(inputs),
        workflow_revision_id=revision_id,
        workflow_snapshot=workflow_data,
        owner_id=actor,
    )

    try:
        report = await execution_engine.execute(
            workflow=workflow_data,
            inputs=inputs,
            execution_id=execution_id,
        )
        ctx = execution_engine.get_context(execution_id)
        exec_service.update_execution_record(
            execution_id,
            report,
            context_dict=ctx.to_dict() if ctx else None,
            workflow_snapshot=workflow_data,
        )
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
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    """Retrieve full execution status, outputs, metrics, and failure information."""
    actor = _resolve_actor(x_user_id, authorization)
    exec_service = ExecutionService(db)
    record = exec_service.get_execution(execution_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution record '{execution_id}' not found.",
        )
    _check_execution_ownership(record, actor)

    return {
        "execution_id": record.id,
        "workflow_id": record.workflow_id,
        "workflow_revision_id": record.workflow_revision_id,
        "status": record.status,
        "input_payload": redact_sensitive_data(record.input_payload),
        "output_result": redact_sensitive_data(record.output_result),
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
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    """Retrieve structured node-level execution trace logs."""
    actor = _resolve_actor(x_user_id, authorization)
    exec_service = ExecutionService(db)
    record = exec_service.get_execution(execution_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution record '{execution_id}' not found.",
        )
    _check_execution_ownership(record, actor)
    return [NodeExecutionLog(**item) for item in (record.logs or [])]


@router.post("/{execution_id}/approve", response_model=ExecutionReportResponse)
async def approve_execution(
    execution_id: str,
    request: ApprovalActionRequest,
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    """Approve a paused human approval step and resume the exact workflow revision."""
    actor = _resolve_actor(x_user_id, authorization)
    exec_service = ExecutionService(db)
    record = exec_service.get_execution(execution_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution record '{execution_id}' not found.",
        )
    _check_execution_ownership(record, actor)

    if record.status != ExecutionStatus.WAITING_FOR_APPROVAL.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Execution '{execution_id}' is in status '{record.status}', not awaiting approval.",
        )

    if not exec_service.claim_for_approval(execution_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Execution '{execution_id}' approval has already been claimed.",
        )

    workflow_dict = _resolve_workflow_snapshot(record, db)
    context = _resolve_execution_context(record)

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
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    """Reject a paused human approval step and terminate execution."""
    actor = _resolve_actor(x_user_id, authorization)
    exec_service = ExecutionService(db)
    record = exec_service.get_execution(execution_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution record '{execution_id}' not found.",
        )
    _check_execution_ownership(record, actor)

    if record.status != ExecutionStatus.WAITING_FOR_APPROVAL.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Execution '{execution_id}' is in status '{record.status}', not awaiting approval.",
        )

    if not exec_service.claim_for_approval(execution_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Execution '{execution_id}' approval has already been claimed.",
        )

    workflow_dict = _resolve_workflow_snapshot(record, db)
    context = _resolve_execution_context(record)

    report = await execution_engine.resume_after_approval(
        workflow=workflow_dict,
        context=context,
        action="reject",
        comment=request.comment or "Approval denied",
        data=request.data,
    )
    exec_service.update_execution_record(execution_id, report, context.to_dict())
    return report


@router.post("/{execution_id}/cancel", response_model=Dict[str, Any])
def cancel_execution(
    execution_id: str,
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    """Cancel a pending or paused execution."""
    actor = _resolve_actor(x_user_id, authorization)
    exec_service = ExecutionService(db)
    record = exec_service.get_execution(execution_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution record '{execution_id}' not found.",
        )
    _check_execution_ownership(record, actor)

    if record.status not in (
        ExecutionStatus.PENDING.value,
        ExecutionStatus.WAITING_FOR_APPROVAL.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Execution '{execution_id}' cannot be cancelled in status '{record.status}'.",
        )

    updated = exec_service.cancel_execution(execution_id)
    return {
        "execution_id": updated.id,
        "status": updated.status,
        "error_message": updated.error_message,
    }
