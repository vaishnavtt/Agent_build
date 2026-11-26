import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Integer
from app.database.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkflowModel(Base):
    """SQLAlchemy model for storing workflow graphs and metadata."""

    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String(120), nullable=False, index=True)
    description = Column(Text, nullable=True)
    version = Column(String(20), default="1.0.0", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Workflow topology definition conforming to shared/workflow.schema.json
    nodes = Column(JSON, nullable=False, default=list)
    edges = Column(JSON, nullable=False, default=list)
    configuration = Column(JSON, nullable=False, default=dict)
    tags = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class WorkflowExecutionModel(Base):
    """SQLAlchemy model tracking runtime execution records and self-repair attempts."""

    __tablename__ = "workflow_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    workflow_id = Column(String(36), nullable=False, index=True)
    status = Column(String(30), default="PENDING", nullable=False, index=True)  # PENDING, RUNNING, COMPLETED, FAILED, REPAIRED
    input_payload = Column(JSON, nullable=True)
    output_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    failed_node_id = Column(String(100), nullable=True)
    repair_attempts = Column(Integer, default=0, nullable=False)

    # Runtime trace, execution logs, and performance metrics
    logs = Column(JSON, nullable=True, default=list)
    metrics = Column(JSON, nullable=True, default=dict)
    execution_context = Column(JSON, nullable=True)  # Checkpoint state for pause and resume

    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

