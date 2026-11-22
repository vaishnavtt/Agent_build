from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.workflow import WorkflowModel, WorkflowExecutionModel, utc_now
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowExecutionCreate,
    WorkflowExecutionUpdate,
)
from app.core.logging import logger


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Helper to guarantee datetime has timezone info for safe arithmetic across SQLite."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class WorkflowService:
    """Service layer for workflow persistence, retrieval, and execution tracking."""

    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------------------
    # WORKFLOW CRUD
    # -------------------------------------------------------------------------

    def get_workflow(
        self, workflow_id: str, include_inactive: bool = False
    ) -> Optional[WorkflowModel]:
        """Fetch a workflow by ID, optionally including inactive/soft-deleted records."""
        query = self.db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id)
        if not include_inactive:
            query = query.filter(
                WorkflowModel.is_active == True,
                WorkflowModel.status != "deleted",
            )
        return query.first()

    def list_workflows(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[WorkflowModel]:
        """List workflows ordered by creation date with pagination and status filters."""
        query = self.db.query(WorkflowModel)
        if not include_inactive:
            query = query.filter(
                WorkflowModel.is_active == True,
                WorkflowModel.status != "deleted",
            )
        if status:
            query = query.filter(WorkflowModel.status == status)

        return (
            query.order_by(WorkflowModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_workflow(self, workflow_in: WorkflowCreate) -> WorkflowModel:
        """Create and persist a new workflow graph conforming to canonical schema."""
        config_dict = (
            workflow_in.configuration.model_dump()
            if hasattr(workflow_in.configuration, "model_dump")
            else dict(workflow_in.configuration or {})
        )

        db_obj = WorkflowModel(
            name=workflow_in.name,
            description=workflow_in.description,
            status=workflow_in.status or "active",
            version=workflow_in.version or "1.0.0",
            is_active=True if (workflow_in.status or "active") != "inactive" else False,
            nodes=workflow_in.nodes or [],
            edges=workflow_in.edges or [],
            configuration=config_dict,
            tags=workflow_in.tags or [],
            workflow_json=workflow_in.workflow_json,
        )

        try:
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)

            # Ensure workflow_json is stored with the generated ID
            if not db_obj.workflow_json:
                db_obj.workflow_json = db_obj.to_canonical_dict()
                self.db.commit()
                self.db.refresh(db_obj)

            logger.info("Created workflow: id=%s, name='%s'", db_obj.id, db_obj.name)
            return db_obj
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("Failed to create workflow: %s", exc)
            raise

    def update_workflow(
        self, workflow_id: str, workflow_in: WorkflowUpdate
    ) -> Optional[WorkflowModel]:
        """Update an existing workflow graph."""
        db_obj = self.get_workflow(workflow_id, include_inactive=True)
        if not db_obj:
            return None

        update_data = workflow_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "configuration" and value is not None:
                db_obj.configuration = (
                    value.model_dump() if hasattr(value, "model_dump") else dict(value)
                )
            elif field == "status" and value is not None:
                db_obj.status = value
                db_obj.is_active = value not in ("inactive", "deleted")
            elif field == "is_active" and value is not None:
                db_obj.is_active = value
                if not value:
                    db_obj.status = "inactive"
            else:
                setattr(db_obj, field, value)

        db_obj.updated_at = utc_now()
        # Synchronize workflow_json to reflect updated fields
        db_obj.workflow_json = db_obj.to_canonical_dict()

        try:
            self.db.commit()
            self.db.refresh(db_obj)
            logger.info("Updated workflow: id=%s", db_obj.id)
            return db_obj
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("Failed to update workflow id=%s: %s", workflow_id, exc)
            raise

    def delete_workflow(self, workflow_id: str, hard_delete: bool = False) -> bool:
        """Delete workflow: soft-delete by default, hard-delete if specified."""
        db_obj = self.get_workflow(workflow_id, include_inactive=True)
        if not db_obj:
            return False

        try:
            if hard_delete:
                self.db.delete(db_obj)
            else:
                db_obj.is_active = False
                db_obj.status = "deleted"
                db_obj.updated_at = utc_now()

            self.db.commit()
            logger.info("Deleted workflow: id=%s (hard=%s)", workflow_id, hard_delete)
            return True
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("Failed to delete workflow id=%s: %s", workflow_id, exc)
            raise

    # -------------------------------------------------------------------------
    # EXECUTION RECORD MANAGEMENT
    # -------------------------------------------------------------------------

    def create_execution(
        self, execution_in: WorkflowExecutionCreate, workflow_id: Optional[str] = None
    ) -> WorkflowExecutionModel:
        """Persist a new execution record for a workflow."""
        target_workflow_id = workflow_id or execution_in.workflow_id
        if not target_workflow_id:
            raise ValueError("workflow_id must be provided to create an execution.")

        # Verify parent workflow exists
        parent_wf = self.get_workflow(target_workflow_id, include_inactive=True)
        if not parent_wf:
            raise ValueError(f"Workflow with ID '{target_workflow_id}' does not exist.")

        status_lower = execution_in.status.lower()
        now = utc_now()
        completed_at = now if status_lower in ("completed", "failed", "repaired") else None

        duration = execution_in.execution_duration
        if duration is None and completed_at:
            duration = 0.0

        exec_obj = WorkflowExecutionModel(
            workflow_id=target_workflow_id,
            status=status_lower,
            input_data=execution_in.input_data or execution_in.input_payload,
            output_data=execution_in.output_data or execution_in.output_result,
            error_message=execution_in.error_message,
            execution_duration=duration,
            repair_attempts=execution_in.repair_attempts,
            started_at=now,
            completed_at=completed_at,
        )

        try:
            self.db.add(exec_obj)
            self.db.commit()
            self.db.refresh(exec_obj)
            logger.info(
                "Created execution: id=%s for workflow_id=%s (status=%s)",
                exec_obj.id,
                target_workflow_id,
                exec_obj.status,
            )
            return exec_obj
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("Failed to record execution: %s", exc)
            raise

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecutionModel]:
        """Retrieve a specific execution record by ID."""
        return (
            self.db.query(WorkflowExecutionModel)
            .filter(WorkflowExecutionModel.id == execution_id)
            .first()
        )

    def update_execution(
        self, execution_id: str, execution_update: WorkflowExecutionUpdate
    ) -> Optional[WorkflowExecutionModel]:
        """Update execution record status, output, duration, or repair attempts."""
        exec_obj = self.get_execution(execution_id)
        if not exec_obj:
            return None

        update_data = execution_update.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "status" and value is not None:
                exec_obj.status = value.lower()
                if exec_obj.status in ("completed", "failed", "repaired") and not exec_obj.completed_at:
                    exec_obj.completed_at = utc_now()
                    if exec_obj.execution_duration is None:
                        start_dt = ensure_utc(exec_obj.started_at)
                        end_dt = ensure_utc(exec_obj.completed_at)
                        if start_dt and end_dt:
                            exec_obj.execution_duration = max(0.0, (end_dt - start_dt).total_seconds())
            elif field in ("output_data", "output_result") and value is not None:
                exec_obj.output_data = value
            else:
                setattr(exec_obj, field, value)

        try:
            self.db.commit()
            self.db.refresh(exec_obj)
            logger.info("Updated execution: id=%s (status=%s)", exec_obj.id, exec_obj.status)
            return exec_obj
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("Failed to update execution id=%s: %s", execution_id, exc)
            raise

    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> List[WorkflowExecutionModel]:
        """Fetch execution history records ordered by started_at descending."""
        query = self.db.query(WorkflowExecutionModel)
        if workflow_id:
            query = query.filter(WorkflowExecutionModel.workflow_id == workflow_id)
        if status:
            query = query.filter(WorkflowExecutionModel.status == status.lower())

        return (
            query.order_by(WorkflowExecutionModel.started_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def delete_execution(self, execution_id: str) -> bool:
        """Delete an execution record."""
        exec_obj = self.get_execution(execution_id)
        if not exec_obj:
            return False

        try:
            self.db.delete(exec_obj)
            self.db.commit()
            return True
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("Failed to delete execution id=%s: %s", execution_id, exc)
            raise
