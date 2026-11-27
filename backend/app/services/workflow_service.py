from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.workflow import WorkflowModel, WorkflowExecutionModel
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate


class WorkflowService:
    """Service layer for workflow persistence, retrieval, and lifecycle management."""

    def __init__(self, db: Session):
        self.db = db

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowModel]:
        """Fetch active workflow by ID."""
        return (
            self.db.query(WorkflowModel)
            .filter(WorkflowModel.id == workflow_id, WorkflowModel.is_active == True)
            .first()
        )

    def list_workflows(self, skip: int = 0, limit: int = 50) -> List[WorkflowModel]:
        """List active workflows with pagination."""
        return (
            self.db.query(WorkflowModel)
            .filter(WorkflowModel.is_active == True)
            .order_by(WorkflowModel.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_workflow(self, workflow_in: WorkflowCreate) -> WorkflowModel:
        """Create and persist a new workflow graph."""
        db_obj = WorkflowModel(
            name=workflow_in.name,
            description=workflow_in.description,
            version=workflow_in.version,
            nodes=[n.model_dump() if hasattr(n, "model_dump") else n for n in workflow_in.nodes],
            edges=[e.model_dump() if hasattr(e, "model_dump") else e for e in workflow_in.edges],
            configuration=workflow_in.configuration.model_dump(),
            tags=workflow_in.tags,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_workflow(self, workflow_id: str, workflow_in: WorkflowUpdate) -> Optional[WorkflowModel]:
        """Update an existing active workflow graph."""
        db_obj = self.get_workflow(workflow_id)
        if not db_obj:
            return None

        update_data = workflow_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete_workflow(self, workflow_id: str) -> bool:
        """Soft-delete workflow by marking inactive."""
        db_obj = self.get_workflow(workflow_id)
        if not db_obj:
            return False
        db_obj.is_active = False
        self.db.commit()
        return True

    def list_executions(
        self, workflow_id: str, skip: int = 0, limit: int = 50
    ) -> List[WorkflowExecutionModel]:
        """List non-candidate executions for a specific workflow."""
        return (
            self.db.query(WorkflowExecutionModel)
            .filter(
                WorkflowExecutionModel.workflow_id == workflow_id,
                WorkflowExecutionModel.is_candidate == False,
            )
            .order_by(WorkflowExecutionModel.started_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
