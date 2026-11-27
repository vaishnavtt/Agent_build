from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    WorkflowRevisionRead,
    WorkflowRevisionDiffResponse,
    WorkflowRevisionPromoteRequest,
    WorkflowRevisionRestoreRequest,
    WorkflowRecoveryReserveRequest,
    WorkflowRecoveryCompleteRequest,
    WorkflowRecoveryRead,
)
from app.core.security import get_current_principal, HostPrincipal, authorize_workflow_owner

router = APIRouter()


# -----------------------------------------------------------------------------
# WORKFLOW CRUD ENDPOINTS (Phase 3 & Phase 6 Security)
# -----------------------------------------------------------------------------

@router.get(
    "",
    response_model=List[WorkflowRead],
    status_code=status.HTTP_200_OK,
    summary="List Workflows",
    description="Retrieve list of active agent workflows scoped to authenticated principal.",
)
def list_workflows(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status (active, inactive, draft)"),
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> List[WorkflowRead]:
    service = WorkflowService(db)
    return service.list_workflows(
        skip=skip,
        limit=limit,
        status=status,
        owner_id=principal.principal_id,
    )


@router.post(
    "",
    response_model=WorkflowRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Workflow",
    description="Persist an authoritative new workflow graph and initialize Revision 1.",
)
def create_workflow(
    workflow_in: WorkflowCreate,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowRead:
    service = WorkflowService(db)
    try:
        return service.create_workflow(workflow_in, creator_id=principal.principal_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


@router.get(
    "/{workflow_id}",
    response_model=WorkflowRead,
    status_code=status.HTTP_200_OK,
    summary="Get Workflow",
    description="Retrieve a specific workflow graph by unique ID with ownership verification.",
)
def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowRead:
    service = WorkflowService(db)
    workflow = service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )
    authorize_workflow_owner(workflow, principal)
    return workflow


@router.put(
    "/{workflow_id}",
    response_model=WorkflowRead,
    status_code=status.HTTP_200_OK,
    summary="Update Workflow",
    description="Atomically update workflow and append a new immutable revision.",
)
def update_workflow(
    workflow_id: str,
    workflow_in: WorkflowUpdate,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowRead:
    service = WorkflowService(db)
    existing = service.get_workflow(workflow_id, include_inactive=True)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )
    authorize_workflow_owner(existing, principal)

    try:
        workflow = service.update_workflow(
            workflow_id=workflow_id,
            workflow_in=workflow_in,
            modifier_id=principal.principal_id,
        )
        return workflow
    except ValueError as exc:
        msg = str(exc)
        if "Conflict:" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)


@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Workflow",
    description="Soft-deletes by default, permanently purges if hard_delete=true.",
)
def delete_workflow(
    workflow_id: str,
    hard_delete: bool = Query(False, description="Permanently purge record and all history"),
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
):
    service = WorkflowService(db)
    existing = service.get_workflow(workflow_id, include_inactive=True)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )
    authorize_workflow_owner(existing, principal)
    service.delete_workflow(workflow_id, hard_delete=hard_delete)
    return None


# -----------------------------------------------------------------------------
# WORKFLOW REVISION ENDPOINTS (Phase 4)
# -----------------------------------------------------------------------------

@router.get(
    "/{workflow_id}/revisions",
    response_model=List[WorkflowRevisionRead],
    status_code=status.HTTP_200_OK,
    summary="List Workflow Revisions",
    description="Retrieve all immutable revisions of a workflow ordered descending.",
)
def list_workflow_revisions(
    workflow_id: str,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> List[WorkflowRevisionRead]:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, include_inactive=True)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    authorize_workflow_owner(wf, principal)
    return service.list_revisions(workflow_id)


@router.get(
    "/{workflow_id}/revisions/last-working",
    response_model=WorkflowRevisionRead,
    status_code=status.HTTP_200_OK,
    summary="Get Last Working Revision",
    description="Retrieve the latest revision with verified passing execution evidence.",
)
def get_last_working_revision(
    workflow_id: str,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowRevisionRead:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, include_inactive=True)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    authorize_workflow_owner(wf, principal)

    last_working = service.get_last_working_revision(workflow_id)
    if not last_working:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No verified working revision found for workflow '{workflow_id}'.",
        )
    return last_working


@router.get(
    "/{workflow_id}/revisions/diff",
    response_model=WorkflowRevisionDiffResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare Two Workflow Revisions via Query",
    description="Calculates node, edge, and configuration differences between two revisions via query parameters.",
)
def compare_workflow_revisions_by_query(
    workflow_id: str,
    from_rev: str = Query(..., alias="from_rev"),
    to_rev: str = Query(..., alias="to_rev"),
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowRevisionDiffResponse:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, include_inactive=True)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    authorize_workflow_owner(wf, principal)

    try:
        return service.diff_revisions(workflow_id, from_rev, to_rev)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/{workflow_id}/revisions/{revision_id}",
    response_model=WorkflowRevisionRead,
    status_code=status.HTTP_200_OK,
    summary="Get Specific Workflow Revision",
    description="Retrieve an immutable revision snapshot by ID.",
)
def get_workflow_revision(
    workflow_id: str,
    revision_id: str,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowRevisionRead:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, include_inactive=True)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    authorize_workflow_owner(wf, principal)

    rev = service.get_revision(workflow_id, revision_id)
    if not rev:
        raise HTTPException(status_code=404, detail=f"Revision '{revision_id}' not found.")
    return rev


@router.post(
    "/{workflow_id}/revisions/{revision_id}/promote",
    response_model=WorkflowRevisionRead,
    status_code=status.HTTP_200_OK,
    summary="Promote Workflow Revision",
    description="Promote revision to active. Requires passing execution evidence.",
)
def promote_workflow_revision(
    workflow_id: str,
    revision_id: str,
    payload: Optional[WorkflowRevisionPromoteRequest] = None,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowRevisionRead:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, include_inactive=True)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    authorize_workflow_owner(wf, principal)

    try:
        exec_id = payload.execution_id if payload else None
        return service.promote_revision(workflow_id, revision_id, execution_id=exec_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_412_PRECONDITION_FAILED, detail=str(exc))


@router.get(
    "/{workflow_id}/revisions/{source_rev_id}/diff/{target_rev_id}",
    response_model=WorkflowRevisionDiffResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare Two Workflow Revisions",
    description="Calculates node, edge, and configuration differences between two revisions.",
)
def compare_workflow_revisions(
    workflow_id: str,
    source_rev_id: str,
    target_rev_id: str,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowRevisionDiffResponse:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, include_inactive=True)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    authorize_workflow_owner(wf, principal)

    try:
        return service.diff_revisions(workflow_id, source_rev_id, target_rev_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{workflow_id}/revisions/{revision_id}/restore",
    response_model=WorkflowRevisionRead,
    status_code=status.HTTP_200_OK,
    summary="Restore Workflow From Revision",
    description="Applies historical snapshot to workflow and appends an incremental revision.",
)
def restore_workflow_revision(
    workflow_id: str,
    revision_id: str,
    payload: Optional[WorkflowRevisionRestoreRequest] = None,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowRevisionRead:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, include_inactive=True)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    authorize_workflow_owner(wf, principal)

    try:
        summary = payload.change_summary if payload else None
        return service.restore_revision(
            workflow_id=workflow_id,
            revision_id=revision_id,
            modifier_id=principal.principal_id,
            summary=summary,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# -----------------------------------------------------------------------------
# DURABLE RECOVERY & REPAIR ENDPOINTS (Phase 5)
# -----------------------------------------------------------------------------

@router.post(
    "/{workflow_id}/recoveries/reserve",
    response_model=WorkflowRecoveryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Reserve Recovery Attempt",
    description="Atomically reserves a recovery attempt adhering strictly to the 2-attempt budget.",
)
def reserve_workflow_recovery(
    workflow_id: str,
    reserve_in: WorkflowRecoveryReserveRequest,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowRecoveryRead:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, include_inactive=True)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    authorize_workflow_owner(wf, principal)

    try:
        return service.reserve_recovery(workflow_id, reserve_in)
    except ValueError as exc:
        err = str(exc)
        if "exceeded" in err.lower() or "limit" in err.lower():
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=err)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err)


@router.post(
    "/{workflow_id}/recoveries/{recovery_id}/complete",
    response_model=WorkflowRecoveryRead,
    status_code=status.HTTP_200_OK,
    summary="Complete Recovery Attempt",
    description="Records recovery completion, status, and proposed patch.",
)
def complete_workflow_recovery(
    workflow_id: str,
    recovery_id: str,
    complete_in: WorkflowRecoveryCompleteRequest,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowRecoveryRead:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, include_inactive=True)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    authorize_workflow_owner(wf, principal)

    try:
        return service.complete_recovery(workflow_id, recovery_id, complete_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{workflow_id}/recoveries/{recovery_id}/promote",
    response_model=WorkflowRecoveryRead,
    status_code=status.HTTP_200_OK,
    summary="Promote Recovery",
    description="Records promotion timestamp when recovery fix is verified.",
)
def promote_workflow_recovery(
    workflow_id: str,
    recovery_id: str,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowRecoveryRead:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, include_inactive=True)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    authorize_workflow_owner(wf, principal)

    try:
        return service.promote_recovery(workflow_id, recovery_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{workflow_id}/recoveries/{recovery_id}/rollback",
    response_model=WorkflowRecoveryRead,
    status_code=status.HTTP_200_OK,
    summary="Rollback Recovery",
    description="Records rollback timestamp when recovery fails verification.",
)
def rollback_workflow_recovery(
    workflow_id: str,
    recovery_id: str,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowRecoveryRead:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, include_inactive=True)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    authorize_workflow_owner(wf, principal)

    try:
        return service.rollback_recovery(workflow_id, recovery_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/{workflow_id}/recoveries",
    response_model=List[WorkflowRecoveryRead],
    status_code=status.HTTP_200_OK,
    summary="List Workflow Recoveries",
    description="Retrieve recovery history for a workflow.",
)
def list_workflow_recoveries(
    workflow_id: str,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> List[WorkflowRecoveryRead]:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, include_inactive=True)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    authorize_workflow_owner(wf, principal)
    return service.list_recoveries(workflow_id)


# -----------------------------------------------------------------------------
# WORKFLOW VALIDATION ENDPOINT
# -----------------------------------------------------------------------------

@router.post(
    "/validate",
    response_model=WorkflowValidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate Workflow Graph",
    description="Validates topology, required connections, node configurations, and calculates readiness score.",
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

    # 3. Check for terminal block (Output or FINISH)
    has_output = any(
        n.get("data", {}).get("componentType") == "Output"
        or n.get("type") == "Output"
        or "output" in n.get("data", {}).get("label", "").lower()
        or "report" in n.get("data", {}).get("label", "").lower()
        for n in nodes
    )
    if nodes and not has_output:
        issues.append(
            {
                "id": "warn-no-output",
                "category": "structural",
                "severity": "warning",
                "title": "Missing Terminal Step",
                "description": "Your agent does not have a designated output step to format results.",
                "suggestedFix": "Add an Output block to present final results.",
            }
        )

    # 4. Check for disconnected nodes if more than 1 node exists
    if len(nodes) > 1:
        connected_node_ids = set()
        for e in edges:
            connected_node_ids.add(e.get("source"))
            connected_node_ids.add(e.get("target"))

        disconnected = [n for n in nodes if n.get("id") not in connected_node_ids]
        for d in disconnected:
            name = d.get("data", {}).get("label") or d.get("name") or d.get("id")
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


# -----------------------------------------------------------------------------
# WORKFLOW EXECUTION TELEMETRY ENDPOINTS
# -----------------------------------------------------------------------------

@router.post(
    "/{workflow_id}/executions",
    response_model=WorkflowExecutionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record Workflow Execution",
    description="Persist runtime execution telemetry in SQLite associated with the workflow.",
)
def record_execution(
    workflow_id: str,
    execution_in: WorkflowExecutionCreate,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowExecutionRead:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, include_inactive=True)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    authorize_workflow_owner(wf, principal)

    try:
        return service.create_execution(execution_in, workflow_id=workflow_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.post(
    "/{workflow_id}/execute",
    response_model=WorkflowExecutionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record Workflow Execution (Legacy Alias)",
    description="Alias endpoint for backward compatibility with existing tests and integration scripts.",
    include_in_schema=False,
)
def record_execution_alias(
    workflow_id: str,
    execution_in: WorkflowExecutionCreate,
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> WorkflowExecutionRead:
    return record_execution(workflow_id=workflow_id, execution_in=execution_in, db=db, principal=principal)


@router.get(
    "/{workflow_id}/executions",
    response_model=List[WorkflowExecutionRead],
    status_code=status.HTTP_200_OK,
    summary="List Workflow Executions",
    description="Retrieve execution history specifically associated with this workflow.",
)
def list_workflow_executions(
    workflow_id: str,
    status: Optional[str] = Query(None, description="Filter by status (case-insensitive: pending, running, completed, failed)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> List[WorkflowExecutionRead]:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, include_inactive=True)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found.",
        )
    authorize_workflow_owner(wf, principal)

    return service.list_executions(
        workflow_id=workflow_id,
        skip=skip,
        limit=limit,
        status=status,
    )


@router.get(
    "/{workflow_id}/revisions/{revision_id}/executions",
    response_model=List[WorkflowExecutionRead],
    status_code=status.HTTP_200_OK,
    summary="List Revision Executions",
    description="Retrieve execution history scoped to a specific immutable revision.",
)
def list_revision_executions(
    workflow_id: str,
    revision_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    principal: HostPrincipal = Depends(get_current_principal),
) -> List[WorkflowExecutionRead]:
    service = WorkflowService(db)
    wf = service.get_workflow(workflow_id, include_inactive=True)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    authorize_workflow_owner(wf, principal)

    return service.list_executions(
        workflow_id=workflow_id,
        revision_id=revision_id,
        skip=skip,
        limit=limit,
        status=status,
    )
