"""Integration adapters for Member 5 (Reliability Lab) and Member 6 (Self-Repair)."""

import copy
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.engine.runner import execution_engine
from app.engine.security import redact_sensitive_data, redact_text
from app.schemas.execution import ExecutionReportResponse, ExecutionStatus
from app.services.execution_service import ExecutionService, compute_workflow_revision_id
from app.services.workflow_service import WorkflowService


def _map_status_to_m5(status: ExecutionStatus, error_message: Optional[str] = None) -> str:
    if status == ExecutionStatus.SUCCESS:
        return "COMPLETED"
    if status == ExecutionStatus.REJECTED:
        return "SAFE_REJECTION"
    if error_message and "timed out" in error_message.lower():
        return "TIMEOUT"
    return "FAILED"


class Member4WorkflowExecutor:
    """Adapter implementing Member 5's IWorkflowExecutor contract with isolated candidate execution."""

    def __init__(self, db_session_factory: Optional[Any] = None):
        self._db_session_factory = db_session_factory

    async def execute(
        self,
        workflow_id: str,
        input_payload: Dict[str, Any],
        workflow_override: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Executes a workflow in isolated candidate mode and returns Member 5 ExecutionResult fields."""
        workflow_dict = copy.deepcopy(workflow_override) if workflow_override else None

        if workflow_dict is None and self._db_session_factory is not None:
            db: Session = self._db_session_factory()
            try:
                wf = WorkflowService(db).get_workflow(workflow_id)
                if wf:
                    workflow_dict = {
                        "id": wf.id,
                        "name": wf.name,
                        "version": wf.version,
                        "nodes": copy.deepcopy(wf.nodes),
                        "edges": copy.deepcopy(wf.edges),
                        "configuration": copy.deepcopy(wf.configuration),
                    }
            finally:
                db.close()

        if workflow_dict is None:
            return {
                "status": "FAILED",
                "output_data": None,
                "execution_trace": [],
                "error": f"Workflow '{workflow_id}' not found.",
                "duration_ms": 0.0,
            }

        try:
            report = await execution_engine.execute(
                workflow=workflow_dict,
                inputs=input_payload,
                candidate_mode=True,
            )
            return {
                "status": _map_status_to_m5(report.status, report.error_message),
                "output_data": redact_sensitive_data(report.result),
                "execution_trace": [log.model_dump() for log in report.node_logs],
                "error": redact_text(report.error_message) if report.error_message else None,
                "duration_ms": report.total_duration_ms,
                "metrics": report.metrics.model_dump(),
            }
        except Exception as exc:
            return {
                "status": "FAILED",
                "output_data": None,
                "execution_trace": [],
                "error": redact_text(str(exc)),
                "duration_ms": 0.0,
            }


class Member4RepairIntegrationAdapter:
    """Adapter providing Member 6 with trusted redacted failure evidence and isolated candidate execution."""

    @staticmethod
    def get_failure_evidence(
        db: Session,
        workflow_id: str,
        workflow_revision_id: str,
        execution_run_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Loads redacted failure evidence and workflow snapshot for a failed execution run."""
        record = ExecutionService(db).get_execution(execution_run_id)
        if not record:
            return None
        if record.workflow_id != workflow_id:
            return None
        if (
            record.workflow_revision_id
            and workflow_revision_id
            and record.workflow_revision_id != workflow_revision_id
        ):
            return None

        snapshot = record.workflow_snapshot or {}
        if not snapshot:
            wf = WorkflowService(db).get_workflow(workflow_id)
            if wf:
                snapshot = {
                    "id": wf.id,
                    "name": wf.name,
                    "version": wf.version,
                    "nodes": wf.nodes,
                    "edges": wf.edges,
                    "configuration": wf.configuration,
                }

        return {
            "workflow_id": record.workflow_id,
            "workflow_revision_id": record.workflow_revision_id or compute_workflow_revision_id(snapshot),
            "execution_run_id": record.id,
            "status": record.status,
            "failed_node_id": record.failed_node_id,
            "error_message": redact_text(record.error_message or ""),
            "node_logs": redact_sensitive_data(record.logs or []),
            "metrics": record.metrics or {},
            "nodes": copy.deepcopy(snapshot.get("nodes", [])),
            "edges": copy.deepcopy(snapshot.get("edges", [])),
        }

    @staticmethod
    async def execute_isolated_candidate(
        candidate_workflow: Dict[str, Any],
        inputs: Dict[str, Any],
        original_duration_ms: Optional[float] = None,
    ) -> ExecutionReportResponse:
        """Executes a candidate workflow deep copy in isolated mode without mutating production state."""
        isolated = copy.deepcopy(candidate_workflow)
        return await execution_engine.execute(
            workflow=isolated,
            inputs=copy.deepcopy(inputs),
            reexecution=True,
            original_duration_ms=original_duration_ms,
            candidate_mode=True,
        )
