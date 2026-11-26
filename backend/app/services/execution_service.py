from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.workflow import WorkflowExecutionModel
from app.schemas.execution import ExecutionReportResponse, ExecutionStatus


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
    ) -> WorkflowExecutionModel:
        record = WorkflowExecutionModel(
            id=execution_id,
            workflow_id=workflow_id,
            status=status.value,
            input_payload=input_payload,
            logs=[],
            metrics={},
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
        if context_dict:
            record.execution_context = context_dict

        if report.end_time:
            try:
                record.completed_at = datetime.fromisoformat(report.end_time)
            except Exception:
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
        self, workflow_id: Optional[str] = None, skip: int = 0, limit: int = 20
    ) -> List[WorkflowExecutionModel]:
        query = self.db.query(WorkflowExecutionModel)
        if workflow_id:
            query = query.filter(WorkflowExecutionModel.workflow_id == workflow_id)
        return query.order_by(WorkflowExecutionModel.started_at.desc()).offset(skip).limit(limit).all()
