import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    JSON,
    Boolean,
    Integer,
    Float,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship, synonym
from app.database.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkflowModel(Base):
    """SQLAlchemy model for storing workflow graphs and metadata.
    
    Adheres to the canonical specification in shared/workflow.schema.json.
    """

    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String(120), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(30), default="active", nullable=False, index=True)  # active, inactive, draft, deleted
    version = Column(String(20), default="1.0.0", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Canonical full structured JSON graph adhering to shared/workflow.schema.json
    workflow_json = Column(JSON, nullable=True)

    # Topology components stored as native JSON for query and frontend compatibility
    nodes = Column(JSON, nullable=False, default=list)
    edges = Column(JSON, nullable=False, default=list)
    configuration = Column(JSON, nullable=False, default=dict)
    tags = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    executions = relationship(
        "WorkflowExecutionModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="desc(WorkflowExecutionModel.started_at)",
    )

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Construct full structured JSON adhering to shared/workflow.schema.json."""
        if self.workflow_json and isinstance(self.workflow_json, dict):
            # Ensure metadata.id matches self.id
            payload = dict(self.workflow_json)
            if "metadata" in payload and isinstance(payload["metadata"], dict):
                payload["metadata"]["id"] = self.id
                payload["metadata"]["name"] = self.name
                payload["metadata"]["description"] = self.description
            return payload

        return {
            "schemaVersion": "1.0.0",
            "metadata": {
                "id": self.id,
                "name": self.name,
                "description": self.description or "",
                "version": self.version or "1.0.0",
                "tags": self.tags or [],
                "author": "AgentForge AI",
                "createdAt": self.created_at.isoformat() if self.created_at else None,
                "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            },
            "configuration": self.configuration or {
                "timeoutSeconds": 300,
                "maxRetries": 2,
                "autoRepairEnabled": True,
                "executionMode": "langgraph",
            },
            "nodes": self.nodes or [],
            "edges": self.edges or [],
        }


class WorkflowExecutionModel(Base):
    """SQLAlchemy model tracking runtime execution records and execution history."""

    __tablename__ = "workflow_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    workflow_id = Column(
        String(36),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(
        String(30),
        default="pending",
        nullable=False,
        index=True,
    )  # pending, running, completed, failed, repaired
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_duration = Column(Float, nullable=True)  # in seconds
    repair_attempts = Column(Integer, default=0, nullable=False)

    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workflow = relationship("WorkflowModel", back_populates="executions")

    # Backward-compatible property synonyms for existing tests & services
    @property
    def input_payload(self) -> Optional[Dict[str, Any]]:
        return self.input_data

    @input_payload.setter
    def input_payload(self, val: Optional[Dict[str, Any]]) -> None:
        self.input_data = val

    @property
    def output_result(self) -> Optional[Dict[str, Any]]:
        return self.output_data

    @output_result.setter
    def output_result(self, val: Optional[Dict[str, Any]]) -> None:
        self.output_data = val


# Multi-column index for execution history queries
Index("ix_executions_workflow_started", WorkflowExecutionModel.workflow_id, WorkflowExecutionModel.started_at.desc())
