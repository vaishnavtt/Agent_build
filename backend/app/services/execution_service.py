import hashlib
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.workflow import WorkflowExecutionModel
from app.schemas.execution import ExecutionReportResponse, ExecutionStatus


def compute_workflow_revision_id(workflow: Dict[str, Any]) -> str:
    """Computes a deterministic immutable revision ID from workflow version and graph topology."""
    explicit_rev = workflow.get("revision_id") or workflow.get("workflow_revision_id")
    if explicit_rev:
        return str(explicit_rev)
    version = str(workflow.get("version") or "1.0.0")
    canonical = json.dumps(
        {
            "version": version,
            "nodes": workflow.get("nodes", []),
            "edges": workflow.get("edges", []),
            "configuration": workflow.get("configuration", {}),
        },
        sort_keys=True,
        default=str,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    return f"{version}-{digest}"


class ExecutionService:
    """Service layer persisting and retrieving execution traces, logs, and checkpoints."""

    def __init__(self, db: Session):
        self.db = db

    def create_execution_record(
        self,
        execution_id: str,
        workflow_id: str,
        input_payload: Dict[str, Any],
        status: ExecutionStatus = ExecutionStatus.PENDING,
        workflow_revision_id: Optional[str] = None,
        workflow_snapshot: Optional[Dict[str, Any]] = None,
        owner_id: Optional[str] = None,
        is_candidate: bool = False,
    ) -> WorkflowExecutionModel:
        record = WorkflowExecutionModel(
            id=execution_id,
            workflow_id=workflow_id,
            workflow_revision_id=workflow_revision_id,
            owner_id=owner_id,
            is_candidate=is_candidate,
            status=status.value,
            input_payload=input_payload,
            logs=[],
            metrics={},
            workflow_snapshot=workflow_snapshot,
            repair_attempts=0,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def update_execution_record(
        self,
        execution_id: str,
        report: ExecutionReportResponse,
        context_dict: Optional[Dict[str, Any]] = None,
        workflow_snapshot: Optional[Dict[str, Any]] = None,
    ) -> Optional[WorkflowExecutionModel]:
        record = (
            self.db.query(WorkflowExecutionModel)
            .filter(WorkflowExecutionModel.id == execution_id)
            .first()
        )
        if not record:
            return None

        record.status = report.status.value
        record.output_result = report.result
        record.error_message = report.error_message
        record.failed_node_id = report.failed_node_id
        record.logs = [log.model_dump() for log in report.node_logs]
        record.metrics = report.metrics.model_dump()
        if context_dict is not None:
            record.execution_context = context_dict
        if workflow_snapshot is not None:
            record.workflow_snapshot = workflow_snapshot

        if report.end_time:
            try:
                record.completed_at = datetime.fromisoformat(report.end_time)
            except Exception:
                record.completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(record)
        return record

    def claim_for_approval(self, execution_id: str) -> bool:
        """Atomically transitions WAITING_FOR_APPROVAL -> RUNNING to prevent duplicate/concurrent approvals."""
        updated = (
            self.db.query(WorkflowExecutionModel)
            .filter(
                WorkflowExecutionModel.id == execution_id,
                WorkflowExecutionModel.status == ExecutionStatus.WAITING_FOR_APPROVAL.value,
            )
            .update({WorkflowExecutionModel.status: ExecutionStatus.RUNNING.value})
        )
        self.db.commit()
        return updated == 1

    def cancel_execution(self, execution_id: str) -> Optional[WorkflowExecutionModel]:
        """Cancels a PENDING or WAITING_FOR_APPROVAL execution."""
        record = self.get_execution(execution_id)
        if not record:
            return None
        if record.status not in (
            ExecutionStatus.PENDING.value,
            ExecutionStatus.WAITING_FOR_APPROVAL.value,
        ):
            return record
        record.status = ExecutionStatus.CANCELLED.value
        record.error_message = "Execution cancelled by user."
        record.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecutionModel]:
        return (
            self.db.query(WorkflowExecutionModel)
            .filter(WorkflowExecutionModel.id == execution_id)
            .first()
        )

    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        include_candidates: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> List[WorkflowExecutionModel]:
        query = self.db.query(WorkflowExecutionModel)
        if workflow_id:
            query = query.filter(WorkflowExecutionModel.workflow_id == workflow_id)
        if owner_id:
            query = query.filter(WorkflowExecutionModel.owner_id == owner_id)
        if not include_candidates:
            query = query.filter(WorkflowExecutionModel.is_candidate == False)
        return (
            query.order_by(WorkflowExecutionModel.started_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
