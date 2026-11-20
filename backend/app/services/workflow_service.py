from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.workflow import WorkflowModel, WorkflowExecutionModel
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowExecutionCreate


class WorkflowService:
    """Service layer for workflow persistence, retrieval, execution recording, and validation."""

    def __init__(self, db: Session):
        self.db = db

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowModel]:
        """Fetch workflow by ID."""
        return (
            self.db.query(WorkflowModel)
            .filter(WorkflowModel.id == workflow_id, WorkflowModel.is_active == True)
            .first()
        )

    def list_workflows(self, skip: int = 0, limit: int = 50) -> List[WorkflowModel]:
        """List active workflows ordered by creation date."""
        return (
            self.db.query(WorkflowModel)
            .filter(WorkflowModel.is_active == True)
            .order_by(WorkflowModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_workflow(self, workflow_in: WorkflowCreate) -> WorkflowModel:
        """Create and persist a new workflow graph in SQLite."""
        db_obj = WorkflowModel(
            name=workflow_in.name,
            description=workflow_in.description,
            version=workflow_in.version,
            nodes=workflow_in.nodes,
            edges=workflow_in.edges,
            configuration=workflow_in.configuration.model_dump()
            if hasattr(workflow_in.configuration, "model_dump")
            else dict(workflow_in.configuration),
            tags=workflow_in.tags,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_workflow(
        self, workflow_id: str, workflow_in: WorkflowUpdate
    ) -> Optional[WorkflowModel]:
        """Update an existing workflow graph."""
        db_obj = self.get_workflow(workflow_id)
        if not db_obj:
            return None

        update_data = workflow_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "configuration" and value is not None:
                db_obj.configuration = (
                    value.model_dump() if hasattr(value, "model_dump") else dict(value)
                )
            else:
                setattr(db_obj, field, value)

        db_obj.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete_workflow(self, workflow_id: str) -> bool:
        """Soft-delete a workflow by setting is_active=False."""
        db_obj = self.get_workflow(workflow_id)
        if not db_obj:
            return False

        db_obj.is_active = False
        db_obj.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def create_execution(
        self, execution_in: WorkflowExecutionCreate
    ) -> WorkflowExecutionModel:
        """Record an execution run and its repair attempts in SQLite."""
        exec_obj = WorkflowExecutionModel(
            workflow_id=execution_in.workflow_id,
            workflow_name=execution_in.workflow_name,
            status=execution_in.status,
            trigger_type=execution_in.trigger_type or "MANUAL",
            input_payload=execution_in.input_payload,
            output_result=execution_in.output_result,
            error_message=execution_in.error_message,
            repair_attempts=execution_in.repair_attempts,
            steps=execution_in.steps or [],
            log_evidence=execution_in.log_evidence or [],
            repair_report=execution_in.repair_report,
            duration=execution_in.duration or "0s",
            completed_at=datetime.now(timezone.utc),
        )
        self.db.add(exec_obj)
        self.db.commit()
        self.db.refresh(exec_obj)
        return exec_obj

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecutionModel]:
        """Fetch a specific execution record by ID."""
        return (
            self.db.query(WorkflowExecutionModel)
            .filter(WorkflowExecutionModel.id == execution_id)
            .first()
        )

    def list_executions(
        self, workflow_id: Optional[str] = None, skip: int = 0, limit: int = 50
    ) -> List[WorkflowExecutionModel]:
        """Fetch execution history records."""
        query = self.db.query(WorkflowExecutionModel)
        if workflow_id:
            query = query.filter(WorkflowExecutionModel.workflow_id == workflow_id)
        return (
            query.order_by(WorkflowExecutionModel.started_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
