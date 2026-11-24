import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
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
    workflow_name = Column(String(120), nullable=True)
    description = Column(Text, nullable=True)
    version = Column(String(20), default="1.0.0", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Workflow topology definition conforming to shared/workflow.schema.json
    nodes = Column(JSON, nullable=False, default=list)
    edges = Column(JSON, nullable=False, default=list)
    configuration = Column(JSON, nullable=False, default=dict)
    workflow_data = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationship to execution history
    executions = relationship(
        "WorkflowExecutionModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
        foreign_keys="[WorkflowExecutionModel.workflow_id]",
    )

    def __init__(self, **kwargs):
        # Sync name and workflow_name
        if "workflow_name" in kwargs and "name" not in kwargs:
            kwargs["name"] = kwargs["workflow_name"]
        elif "name" in kwargs and "workflow_name" not in kwargs:
            kwargs["workflow_name"] = kwargs["name"]

        # Sync workflow_data and nodes/edges
        if "workflow_data" in kwargs and kwargs["workflow_data"] and isinstance(kwargs["workflow_data"], dict):
            wf_data = kwargs["workflow_data"]
            if "nodes" not in kwargs:
                kwargs["nodes"] = wf_data.get("nodes", [])
            if "edges" not in kwargs:
                kwargs["edges"] = wf_data.get("edges", [])
            if "configuration" not in kwargs:
                kwargs["configuration"] = wf_data.get("configuration", {})

        super().__init__(**kwargs)
        if not self.workflow_name:
            self.workflow_name = self.name
        if not self.workflow_data:
            self.workflow_data = {
                "nodes": self.nodes or [],
                "edges": self.edges or [],
                "configuration": self.configuration or {},
            }


class WorkflowExecutionModel(Base):
    """SQLAlchemy model tracking runtime execution records and self-repair attempts."""

    __tablename__ = "workflow_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_name = Column(String(120), nullable=True)
    status = Column(String(30), default="PENDING", nullable=False, index=True)  # PENDING, RUNNING, COMPLETED, FAILED
    execution_status = Column(String(30), default="Pending", nullable=True)
    trigger_type = Column(String(50), default="MANUAL", nullable=False)
    input_payload = Column(JSON, nullable=True)
    output_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    repair_attempts = Column(Integer, default=0, nullable=False)
    steps = Column(JSON, nullable=False, default=list)
    log_evidence = Column(JSON, nullable=False, default=list)
    execution_logs = Column(JSON, nullable=True)
    repair_report = Column(JSON, nullable=True)
    duration = Column(String(30), nullable=True, default="0s")

    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    start_time = Column(DateTime(timezone=True), default=utc_now, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)

    # Relationship to parent workflow
    workflow = relationship("WorkflowModel", back_populates="executions")

    def __init__(self, **kwargs):
        # Sync status and execution_status
        if "execution_status" in kwargs and "status" not in kwargs:
            kwargs["status"] = kwargs["execution_status"].upper()
        elif "status" in kwargs and "execution_status" not in kwargs:
            kwargs["execution_status"] = kwargs["status"].capitalize()

        # Sync started_at and start_time
        if "start_time" in kwargs and "started_at" not in kwargs:
            kwargs["started_at"] = kwargs["start_time"]
        elif "started_at" in kwargs and "start_time" not in kwargs:
            kwargs["start_time"] = kwargs["started_at"]

        # Sync completed_at and end_time
        if "end_time" in kwargs and "completed_at" not in kwargs:
            kwargs["completed_at"] = kwargs["end_time"]
        elif "completed_at" in kwargs and "end_time" not in kwargs:
            kwargs["end_time"] = kwargs["completed_at"]

        # Sync log_evidence and execution_logs
        if "execution_logs" in kwargs and "log_evidence" not in kwargs:
            kwargs["log_evidence"] = kwargs["execution_logs"]
        elif "log_evidence" in kwargs and "execution_logs" not in kwargs:
            kwargs["execution_logs"] = kwargs["log_evidence"]

        super().__init__(**kwargs)
        if not self.execution_status and self.status:
            self.execution_status = self.status.capitalize()
        if not self.start_time and self.started_at:
            self.start_time = self.started_at
        if not self.end_time and self.completed_at:
            self.end_time = self.completed_at
        if self.execution_logs is None and self.log_evidence is not None:
            self.execution_logs = self.log_evidence


# Convenient alias for execution history
ExecutionHistoryModel = WorkflowExecutionModel
