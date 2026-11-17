from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.workflow import WorkflowModel
from app.schemas.workflow import WorkflowCreate


class WorkflowService:
    """Service layer for workflow persistence, retrieval, and validation."""

    def __init__(self, db: Session):
        self.db = db

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowModel]:
        """Fetch workflow by ID."""
        return (
            self.db.query(WorkflowModel)
            .filter(WorkflowModel.id == workflow_id, WorkflowModel.is_active == True)
            .first()
        )

    def list_workflows(self, skip: int = 0, limit: int = 20) -> List[WorkflowModel]:
        """List active workflows with pagination."""
        return (
            self.db.query(WorkflowModel)
            .filter(WorkflowModel.is_active == True)
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
            nodes=[n.model_dump() for n in workflow_in.nodes],
            edges=[e.model_dump() for e in workflow_in.edges],
            configuration=workflow_in.configuration.model_dump(),
            tags=workflow_in.tags,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

