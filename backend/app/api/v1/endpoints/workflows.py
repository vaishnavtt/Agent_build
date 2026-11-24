from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
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
from app.agents.validation_agent import ValidationAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.execution_agent import ExecutionAgent

router = APIRouter()


class WorkflowRunRequest(BaseModel):
    input_payload: Optional[Dict[str, Any]] = None
    auto_repair: bool = True


class WorkflowRunAdhocRequest(BaseModel):
    name: Optional[str] = "AgentForge Workflow"
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    input_payload: Optional[Dict[str, Any]] = None
    auto_repair: bool = True


class WorkflowPlanRequest(BaseModel):
    prompt: str = Field(..., min_length=3)
    requirements: Optional[List[str]] = None


# --- Workflow CRUD Endpoints ---


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
    "/executions/all",
    response_model=List[WorkflowExecutionRead],
    status_code=status.HTTP_200_OK,
    summary="List All Executions",
    description="Retrieve execution history across all workflows.",
)
def list_all_executions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[WorkflowExecutionRead]:
    service = WorkflowService(db)
    return service.list_executions(workflow_id=None, skip=skip, limit=limit)


@router.get(
    "/executions/{execution_id}",
    response_model=WorkflowExecutionRead,
    status_code=status.HTTP_200_OK,
    summary="Get Execution Record",
    description="Retrieve a specific execution record by its ID with full log evidence.",
)
def get_execution(
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


@router.post(
    "/plan",
    status_code=status.HTTP_200_OK,
    summary="Plan Workflow with Planner Agent",
    description="Deconstructs natural language requirements into a valid workflow graph.",
)
def plan_workflow_endpoint(
    payload: WorkflowPlanRequest,
) -> Dict[str, Any]:
    planner = PlannerAgent()
    return planner.plan_workflow(payload.prompt, payload.requirements)


@router.post(
    "/validate",
    response_model=WorkflowValidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate Workflow Graph",
    description="Validates topology, required connections, and node configurations using Validation Agent.",
)
def validate_workflow(
    payload: WorkflowValidateRequest,
) -> WorkflowValidateResponse:
    agent = ValidationAgent()
    res = agent.validate_workflow(payload.nodes, payload.edges)
    return WorkflowValidateResponse(
        is_valid=res["is_valid"],
        readiness_score=res["readiness_score"],
        issues=res["issues"],
        metrics=res["metrics"],
    )


@router.post(
    "/run-adhoc",
    response_model=WorkflowExecutionRead,
    status_code=status.HTTP_200_OK,
    summary="Execute Adhoc Workflow Canvas",
    description="Executes a live workflow graph directly from the React Flow editor.",
)
def run_adhoc_workflow(
    payload: WorkflowRunAdhocRequest,
    db: Session = Depends(get_db),
) -> WorkflowExecutionRead:
    agent = ExecutionAgent()
    wf_dict = {
        "id": "adhoc-canvas",
        "name": payload.name or "Adhoc Canvas Agent",
        "nodes": payload.nodes,
        "edges": payload.edges,
    }
    exec_res = agent.execute_workflow(
        workflow=wf_dict,
        input_payload=payload.input_payload,
        auto_repair=payload.auto_repair,
    )

    # Persist execution run in database
    service = WorkflowService(db)
    exec_in = WorkflowExecutionCreate(
        workflow_id="adhoc-canvas",
        workflow_name=payload.name or "Adhoc Canvas Agent",
        status=exec_res["status"],
        trigger_type="STUDIO_RUN",
        input_payload=exec_res["input_payload"],
        output_result=exec_res["output_result"],
        error_message=exec_res.get("error_message"),
        repair_attempts=exec_res.get("repair_attempts", 0),
        steps=exec_res.get("steps", []),
        log_evidence=exec_res.get("log_evidence", []),
        repair_report=exec_res.get("repair_report"),
        duration=exec_res.get("duration", "0s"),
    )
    return service.create_execution(exec_in)


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
    "/{workflow_id}/run",
    response_model=WorkflowExecutionRead,
    status_code=status.HTTP_200_OK,
    summary="Run Workflow with Execution Agent",
    description="Runs the full multi-agent workflow execution pipeline with logging and autonomous self-repair.",
)
def run_workflow(
    workflow_id: str,
    payload: WorkflowRunRequest,
    db: Session = Depends(get_db),
) -> WorkflowExecutionRead:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )

    wf_dict = {
        "id": wf.id,
        "name": wf.name,
        "nodes": wf.nodes,
        "edges": wf.edges,
    }

    agent = ExecutionAgent()
    exec_res = agent.execute_workflow(
        workflow=wf_dict,
        input_payload=payload.input_payload,
        auto_repair=payload.auto_repair,
    )

    exec_in = WorkflowExecutionCreate(
        workflow_id=wf.id,
        workflow_name=wf.name,
        status=exec_res["status"],
        trigger_type="STUDIO_RUN",
        input_payload=exec_res["input_payload"],
        output_result=exec_res["output_result"],
        error_message=exec_res.get("error_message"),
        repair_attempts=exec_res.get("repair_attempts", 0),
        steps=exec_res.get("steps", []),
        log_evidence=exec_res.get("log_evidence", []),
        repair_report=exec_res.get("repair_report"),
        duration=exec_res.get("duration", "0s"),
    )
    return service.create_execution(exec_in)


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
    description="Get execution history for a specific workflow.",
)
def list_workflow_executions(
    workflow_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[WorkflowExecutionRead]:
    service = WorkflowService(db)
    return service.list_executions(workflow_id=workflow_id, skip=skip, limit=limit)


@router.get(
    "/{workflow_id}/history",
    response_model=List[WorkflowExecutionRead],
    status_code=status.HTTP_200_OK,
    summary="Get Workflow Execution History",
    description="Retrieve execution history records for a specific workflow.",
)
def get_workflow_history(
    workflow_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[WorkflowExecutionRead]:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )
    return service.get_execution_history(workflow_id=workflow_id, skip=skip, limit=limit)


@router.post(
    "/{workflow_id}/validate",
    response_model=WorkflowValidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate Saved Workflow Structure & Connections",
    description="Validates topology, node completeness, and connection rules of a specific saved workflow.",
)
def validate_saved_workflow(
    workflow_id: str,
    payload: Optional[WorkflowValidateRequest] = None,
    db: Session = Depends(get_db),
) -> WorkflowValidateResponse:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )

    nodes = (payload.nodes if payload and payload.nodes is not None else None) or wf.nodes or []
    edges = (payload.edges if payload and payload.edges is not None else None) or wf.edges or []
    agent = ValidationAgent()
    res = agent.validate_workflow(nodes, edges)
    return WorkflowValidateResponse(
        is_valid=res["is_valid"],
        readiness_score=res["readiness_score"],
        issues=res["issues"],
        metrics=res["metrics"],
    )
