import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.session import get_db
from app.services.workflow_service import WorkflowService
from app.services.execution_service import ExecutionService, compute_workflow_revision_id
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowRead,
    WorkflowUpdate,
    WorkflowValidateRequest,
    WorkflowValidateResponse,
    WorkflowExecutionRead,
)
from app.schemas.execution import WorkflowExecuteRequest, ExecutionReportResponse
from app.engine.runner import execution_engine
from app.engine.types import ExecutionEngineError

router = APIRouter(prefix="/workflows", tags=["Workflows"])


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
    limit: int = 50,
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


@router.put("/{workflow_id}", response_model=WorkflowRead)
def update_workflow(
    workflow_id: str,
    workflow_in: WorkflowUpdate,
    db: Session = Depends(get_db),
):
    """Update workflow configuration, nodes, and edges."""
    service = WorkflowService(db)
    workflow = service.update_workflow(workflow_id, workflow_in)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )
    return workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
):
    """Soft-delete workflow graph by marking it inactive."""
    service = WorkflowService(db)
    if not service.delete_workflow(workflow_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )
    return None


@router.post("/validate", response_model=WorkflowValidateResponse)
def validate_workflow(payload: WorkflowValidateRequest) -> WorkflowValidateResponse:
    """Validates topology, required connections, and node configurations."""
    nodes = payload.nodes
    edges = payload.edges
    issues = []

    if not nodes:
        issues.append(
            {
                "id": "err-no-nodes",
                "category": "structural",
                "severity": "error",
                "title": "No Components in Workflow",
                "description": "The workflow contains no building blocks.",
                "suggestedFix": "Add at least one START block and one FINISH block.",
            }
        )

    has_start = any(
        n.get("data", {}).get("componentType") == "Input"
        or n.get("type") == "Input"
        or n.get("data", {}).get("label", "").lower() == "start"
        for n in nodes
    )
    if nodes and not has_start:
        issues.append(
            {
                "id": "warn-no-start",
                "category": "structural",
                "severity": "warning",
                "title": "Missing Start Step",
                "description": "Your agent does not have a designated entry step.",
                "suggestedFix": "Add a START (Input) block to capture incoming information.",
            }
        )

    if len(nodes) > 1:
        connected_node_ids = set()
        for e in edges:
            connected_node_ids.add(e.get("source"))
            connected_node_ids.add(e.get("target"))
        for d in nodes:
            if d.get("id") not in connected_node_ids:
                name = d.get("name") or d.get("data", {}).get("label") or d.get("id")
                issues.append(
                    {
                        "id": f"conn-{d.get('id')}",
                        "nodeId": d.get("id"),
                        "category": "connection",
                        "severity": "warning",
                        "title": f"'{name}' is Disconnected",
                        "description": "This step is not linked to any other step in the workflow.",
                        "suggestedFix": "Drag a connector line to link this step into your agent's flow.",
                    }
                )

    is_valid = not any(i["severity"] == "error" for i in issues)
    error_count = sum(1 for i in issues if i["severity"] == "error")
    warn_count = sum(1 for i in issues if i["severity"] == "warning")
    score = max(0, 100 - (error_count * 30 + warn_count * 10))

    return WorkflowValidateResponse(
        is_valid=is_valid,
        readiness_score=score,
        issues=issues,
        metrics={
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "errors": error_count,
            "warnings": warn_count,
        },
    )


@router.post("/{workflow_id}/execute", response_model=ExecutionReportResponse)
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    """Execute a persisted visual workflow graph by its ID using an immutable snapshot."""
    actor = _resolve_actor(x_user_id, authorization)
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
    revision_id = compute_workflow_revision_id(workflow_dict)

    execution_id = str(uuid.uuid4())
    exec_service.create_execution_record(
        execution_id=execution_id,
        workflow_id=workflow.id,
        input_payload=request.inputs,
        workflow_revision_id=revision_id,
        workflow_snapshot=workflow_dict,
        owner_id=actor,
    )

    try:
        report = await execution_engine.execute(
            workflow=workflow_dict,
            inputs=request.inputs,
            execution_id=execution_id,
        )
        ctx = execution_engine.get_context(execution_id)
        exec_service.update_execution_record(
            execution_id,
            report,
            context_dict=ctx.to_dict() if ctx else None,
            workflow_snapshot=workflow_dict,
        )
        return report
    except ExecutionEngineError as ee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": ee.message, "node_id": ee.node_id, "stage": ee.stage},
        )


@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecutionRead])
def list_workflow_executions(
    workflow_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Get execution history for a workflow."""
    service = WorkflowService(db)
    return service.list_executions(workflow_id=workflow_id, skip=skip, limit=limit)
