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
        name = workflow_in.workflow_name or workflow_in.name or "Untitled Workflow"
        nodes = workflow_in.nodes or []
        edges = workflow_in.edges or []
        config = (
            workflow_in.configuration.model_dump()
            if hasattr(workflow_in.configuration, "model_dump")
            else dict(workflow_in.configuration)
        )
        wf_data = workflow_in.workflow_data or {
            "nodes": nodes,
            "edges": edges,
            "configuration": config,
        }

        db_obj = WorkflowModel(
            name=name,
            workflow_name=name,
            description=workflow_in.description,
            version=workflow_in.version,
            nodes=nodes,
            edges=edges,
            configuration=config,
            workflow_data=wf_data,
            tags=workflow_in.tags or [],
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
            elif field in ("workflow_name", "name") and value is not None:
                db_obj.name = value
                db_obj.workflow_name = value
            elif field == "workflow_data" and value is not None and isinstance(value, dict):
                db_obj.workflow_data = value
                if "nodes" in value:
                    db_obj.nodes = value["nodes"]
                if "edges" in value:
                    db_obj.edges = value["edges"]
            else:
                setattr(db_obj, field, value)

        # Update workflow_data cache
        db_obj.workflow_data = {
            "nodes": db_obj.nodes,
            "edges": db_obj.edges,
            "configuration": db_obj.configuration,
        }
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
        now = datetime.now(timezone.utc)
        start_time = execution_in.start_time or execution_in.started_at or now
        end_time = execution_in.end_time or execution_in.completed_at or now
        logs = execution_in.execution_logs if execution_in.execution_logs is not None else execution_in.log_evidence

        exec_obj = WorkflowExecutionModel(
            workflow_id=execution_in.workflow_id,
            workflow_name=execution_in.workflow_name,
            status=execution_in.status,
            execution_status=execution_in.execution_status or execution_in.status.capitalize(),
            trigger_type=execution_in.trigger_type or "MANUAL",
            input_payload=execution_in.input_payload,
            output_result=execution_in.output_result,
            error_message=execution_in.error_message,
            repair_attempts=execution_in.repair_attempts,
            steps=execution_in.steps or [],
            log_evidence=execution_in.log_evidence or [],
            execution_logs=logs or [],
            repair_report=execution_in.repair_report,
            duration=execution_in.duration or "0s",
            started_at=start_time,
            start_time=start_time,
            completed_at=end_time,
            end_time=end_time,
        )
        self.db.add(exec_obj)
        self.db.commit()
        self.db.refresh(exec_obj)
        return exec_obj

    def get_execution_history(
        self, workflow_id: str, skip: int = 0, limit: int = 50
    ) -> List[WorkflowExecutionModel]:
        """Fetch execution history for a specific workflow."""
        return self.list_executions(workflow_id=workflow_id, skip=skip, limit=limit)

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
