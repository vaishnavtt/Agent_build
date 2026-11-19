from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.workflow_service import WorkflowService
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowRead,
    WorkflowUpdate,
    WorkflowValidateRequest,
    WorkflowValidateResponse,
    WorkflowExecutionCreate,
    WorkflowExecutionRead,
)

router = APIRouter()


@router.get(
    "",
    response_model=List[WorkflowRead],
    status_code=status.HTTP_200_OK,
    summary="List Workflows",
    description="Retrieve list of active agent workflows stored in SQLite.",
)
def list_workflows(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[WorkflowRead]:
    service = WorkflowService(db)
    return service.list_workflows(skip=skip, limit=limit)


@router.post(
    "",
    response_model=WorkflowRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Workflow",
    description="Persist a new agent workflow graph into SQLite.",
)
def create_workflow(
    workflow_in: WorkflowCreate,
    db: Session = Depends(get_db),
) -> WorkflowRead:
    service = WorkflowService(db)
    return service.create_workflow(workflow_in)


@router.get(
    "/{workflow_id}",
    response_model=WorkflowRead,
    status_code=status.HTTP_200_OK,
    summary="Get Workflow",
    description="Retrieve a specific workflow graph by its unique ID.",
)
def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
) -> WorkflowRead:
    service = WorkflowService(db)
    workflow = service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )
    return workflow


@router.put(
    "/{workflow_id}",
    response_model=WorkflowRead,
    status_code=status.HTTP_200_OK,
    summary="Update Workflow",
    description="Update workflow configuration, nodes, and edges.",
)
def update_workflow(
    workflow_id: str,
    workflow_in: WorkflowUpdate,
    db: Session = Depends(get_db),
) -> WorkflowRead:
    service = WorkflowService(db)
    workflow = service.update_workflow(workflow_id, workflow_in)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )
    return workflow


@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Workflow",
    description="Soft-delete workflow graph by marking it inactive.",
)
def delete_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
):
    service = WorkflowService(db)
    success = service.delete_workflow(workflow_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )
    return None


@router.post(
    "/validate",
    response_model=WorkflowValidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate Workflow Graph",
    description="Validates topology, required connections, and node configurations.",
)
def validate_workflow(
    payload: WorkflowValidateRequest,
) -> WorkflowValidateResponse:
    nodes = payload.nodes
    edges = payload.edges

    issues = []
    # 1. Structural check: Must have at least 1 node
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

    # 2. Check for start block (Input or START)
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

    # 3. Check for disconnected nodes if more than 1 node exists
    if len(nodes) > 1:
        connected_node_ids = set()
        for e in edges:
            connected_node_ids.add(e.get("source"))
            connected_node_ids.add(e.get("target"))

        disconnected = [n for n in nodes if n.get("id") not in connected_node_ids]
        for d in disconnected:
            name = d.get("data", {}).get("label") or d.get("id")
            issues.append(
                {
                    "id": f"conn-{d.get('id')}",
                    "nodeId": d.get("id"),
                    "category": "connection",
                    "severity": "warning",
                    "title": f"'{name}' is Disconnected",
                    "description": f"This step is not linked to any other step in the workflow.",
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


@router.post(
    "/{workflow_id}/execute",
    response_model=WorkflowExecutionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record Workflow Execution",
    description="Persist runtime execution telemetry in SQLite.",
)
def record_execution(
    workflow_id: str,
    execution_in: WorkflowExecutionCreate,
    db: Session = Depends(get_db),
) -> WorkflowExecutionRead:
    service = WorkflowService(db)
    # Ensure workflow exists
    wf = service.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )
    return service.create_execution(execution_in)


@router.get(
    "/{workflow_id}/executions",
    response_model=List[WorkflowExecutionRead],
    status_code=status.HTTP_200_OK,
    summary="List Workflow Executions",
    description="Get execution history for a workflow.",
)
def list_workflow_executions(
    workflow_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[WorkflowExecutionRead]:
    service = WorkflowService(db)
    return service.list_executions(workflow_id=workflow_id, skip=skip, limit=limit)
