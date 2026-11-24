"""SQLAlchemy database models for AgentForge AI.

Defines:
- WorkflowModel (Table: workflows)
- WorkflowExecutionModel / ExecutionHistoryModel (Table: workflow_executions)
With established relationship between workflows and execution history.
"""

from app.models.workflow import (
    WorkflowModel,
    WorkflowExecutionModel,
    ExecutionHistoryModel,
    generate_uuid,
    utc_now,
)

__all__ = [
    "WorkflowModel",
    "WorkflowExecutionModel",
    "ExecutionHistoryModel",
    "generate_uuid",
    "utc_now",
]
