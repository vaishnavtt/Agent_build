"""CRUD operations for Workflows and Execution History in AgentForge AI."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.services.workflow_service import WorkflowService
from app.models.workflow import WorkflowModel, WorkflowExecutionModel
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowExecutionCreate


def get_workflow(db: Session, workflow_id: str) -> Optional[WorkflowModel]:
    """Retrieve a single active workflow by ID."""
    return WorkflowService(db).get_workflow(workflow_id)


def get_workflows(db: Session, skip: int = 0, limit: int = 50) -> List[WorkflowModel]:
    """Retrieve all active workflows ordered by creation date."""
    return WorkflowService(db).list_workflows(skip=skip, limit=limit)


list_workflows = get_workflows


def create_workflow(db: Session, workflow_in: WorkflowCreate) -> WorkflowModel:
    """Create and persist a new workflow graph in SQLite."""
    return WorkflowService(db).create_workflow(workflow_in)


def update_workflow(
    db: Session, workflow_id: str, workflow_in: WorkflowUpdate
) -> Optional[WorkflowModel]:
    """Update an existing workflow graph."""
    return WorkflowService(db).update_workflow(workflow_id, workflow_in)


def delete_workflow(db: Session, workflow_id: str) -> bool:
    """Soft delete workflow by ID."""
    return WorkflowService(db).delete_workflow(workflow_id)


def create_execution(
    db: Session, execution_in: WorkflowExecutionCreate
) -> WorkflowExecutionModel:
    """Record a workflow execution run in SQLite."""
    return WorkflowService(db).create_execution(execution_in)


def get_execution(db: Session, execution_id: str) -> Optional[WorkflowExecutionModel]:
    """Fetch execution record by ID."""
    return WorkflowService(db).get_execution(execution_id)


def get_workflow_executions(
    db: Session, workflow_id: str, skip: int = 0, limit: int = 50
) -> List[WorkflowExecutionModel]:
    """Fetch execution history for a specific workflow."""
    return WorkflowService(db).get_execution_history(workflow_id, skip=skip, limit=limit)


get_execution_history = get_workflow_executions


def get_all_executions(
    db: Session, skip: int = 0, limit: int = 50
) -> List[WorkflowExecutionModel]:
    """Fetch all execution records across all workflows."""
    return WorkflowService(db).list_executions(workflow_id=None, skip=skip, limit=limit)
