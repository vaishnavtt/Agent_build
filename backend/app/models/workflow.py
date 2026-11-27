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

    # Ownership & Security
    owner_id = Column(String(100), default="default-owner", nullable=False, index=True)

    # Revisions tracking
    active_revision_id = Column(String(36), nullable=True, index=True)
    current_revision_number = Column(Integer, default=1, nullable=False)

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
    revisions = relationship(
        "WorkflowRevisionModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="desc(WorkflowRevisionModel.revision_number)",
    )
    recoveries = relationship(
        "WorkflowRecoveryModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="desc(WorkflowRecoveryModel.reserved_at)",
    )

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Construct full structured JSON adhering to shared/workflow.schema.json."""
        if self.workflow_json and isinstance(self.workflow_json, dict):
            payload = dict(self.workflow_json)
            if "metadata" in payload and isinstance(payload["metadata"], dict):
                payload["metadata"]["id"] = self.id
                payload["metadata"]["name"] = self.name
                payload["metadata"]["description"] = self.description
                payload["metadata"]["version"] = self.version
                payload["metadata"]["tags"] = self.tags or []
                payload["metadata"]["ownerId"] = self.owner_id
                payload["metadata"]["activeRevisionId"] = self.active_revision_id
                payload["metadata"]["currentRevisionNumber"] = self.current_revision_number
                payload["metadata"]["updatedAt"] = (
                    self.updated_at.isoformat() if self.updated_at else None
                )
            payload["nodes"] = self.nodes or []
            payload["edges"] = self.edges or []
            payload["configuration"] = self.configuration or {}
            return payload

        return {
            "schemaVersion": "1.0.0",
            "metadata": {
                "id": self.id,
                "name": self.name,
                "description": self.description or "",
                "version": self.version or "1.0.0",
                "tags": self.tags or [],
                "author": self.owner_id or "AgentForge AI",
                "ownerId": self.owner_id or "default-owner",
                "activeRevisionId": self.active_revision_id,
                "currentRevisionNumber": self.current_revision_number,
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


class WorkflowRevisionModel(Base):
    """SQLAlchemy model tracking immutable workflow graph revisions.
    
    Revisions are strictly append-only. Previously created revisions are never mutated.
    """

    __tablename__ = "workflow_revisions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    workflow_id = Column(
        String(36),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    revision_number = Column(Integer, nullable=False, index=True)
    version = Column(String(20), default="1.0.0", nullable=False)
    snapshot = Column(JSON, nullable=False)  # Canonical workflow JSON snapshot
    change_summary = Column(Text, nullable=True)
    created_by = Column(String(100), default="default-owner", nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # Requires passing execution evidence
    last_execution_id = Column(String(36), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    workflow = relationship("WorkflowModel", back_populates="revisions")
    executions = relationship("WorkflowExecutionModel", back_populates="revision")
    recoveries = relationship("WorkflowRecoveryModel", back_populates="revision")


class WorkflowRecoveryModel(Base):
    """SQLAlchemy model tracking durable recovery attempts and repair life cycle."""

    __tablename__ = "workflow_recoveries"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    workflow_id = Column(
        String(36),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    revision_id = Column(
        String(36),
        ForeignKey("workflow_revisions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    execution_id = Column(
        String(36),
        ForeignKey("workflow_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    attempt_number = Column(Integer, nullable=False, default=1)
    status = Column(
        String(30),
        default="reserved",
        nullable=False,
        index=True,
    )  # reserved, in_progress, completed, failed, cancelled, promoted, rolled_back
    idempotency_key = Column(String(100), unique=True, index=True, nullable=True)
    error_context = Column(JSON, nullable=True)
    proposed_patch = Column(JSON, nullable=True)

    reserved_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    promoted_at = Column(DateTime(timezone=True), nullable=True)
    rolled_back_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workflow = relationship("WorkflowModel", back_populates="recoveries")
    revision = relationship("WorkflowRevisionModel", back_populates="recoveries")


class WorkflowExecutionModel(Base):
    """SQLAlchemy model tracking runtime execution telemetry and recovery links."""

    __tablename__ = "workflow_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    workflow_id = Column(
        String(36),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    revision_id = Column(
        String(36),
        ForeignKey("workflow_revisions.id", ondelete="SET NULL"),
        nullable=True,
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

    # Telemetry & Monitoring (Phase 6)
    node_logs = Column(JSON, nullable=True, default=list)
    token_usage = Column(JSON, nullable=True)  # dict: {prompt_tokens, completion_tokens, total_tokens}
    ai_provider = Column(String(50), nullable=True)
    ai_model = Column(String(100), nullable=True)
    estimated_cost = Column(Float, nullable=True)
    reliability_report = Column(JSON, nullable=True)
    repair_report = Column(JSON, nullable=True)

    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workflow = relationship("WorkflowModel", back_populates="executions")
    revision = relationship("WorkflowRevisionModel", back_populates="executions")

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
Index("ix_executions_revision_started", WorkflowExecutionModel.revision_id, WorkflowExecutionModel.started_at.desc())
Index("ix_revisions_workflow_num", WorkflowRevisionModel.workflow_id, WorkflowRevisionModel.revision_number.desc())
Index("ix_recoveries_workflow_attempt", WorkflowRecoveryModel.workflow_id, WorkflowRecoveryModel.attempt_number)
