from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator

NodeType = Literal[
    "Input",
    "LLM",
    "Document Reader",
    "Tool",
    "Condition",
    "Human Approval",
    "Output",
]


class NodePosition(BaseModel):
    x: float
    y: float


class WorkflowNodeSchema(BaseModel):
    id: str
    type: Optional[str] = "customWorkflow"
    name: Optional[str] = None
    position: Optional[NodePosition] = None
    data: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    inputHandles: Optional[List[str]] = Field(default_factory=list)
    outputHandles: Optional[List[str]] = Field(default_factory=list)


class WorkflowEdgeSchema(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    condition: Optional[str] = None
    animated: Optional[bool] = True


class WorkflowConfigurationSchema(BaseModel):
    timeoutSeconds: int = Field(default=300, ge=1, le=3600)
    maxRetries: int = Field(default=2, ge=0, le=5)
    autoRepairEnabled: bool = True
    executionMode: Literal["sequential", "dag", "langgraph"] = "langgraph"


class WorkflowBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None
    status: Optional[str] = "active"
    version: str = "1.0.0"
    workflow_json: Optional[Dict[str, Any]] = None
    configuration: WorkflowConfigurationSchema = Field(default_factory=WorkflowConfigurationSchema)
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class WorkflowCreate(WorkflowBase):
    """Schema for creating a workflow."""

    owner_id: Optional[str] = None
    change_summary: Optional[str] = "Initial workflow creation"

    @model_validator(mode="before")
    @classmethod
    def parse_canonical_format(cls, data: Any) -> Any:
        """Allow ingesting either standard flat payload or shared/workflow.schema.json canonical structure."""
        if isinstance(data, dict):
            # If input conforms directly to shared/workflow.schema.json
            if "metadata" in data and "nodes" in data and "edges" in data:
                meta = data.get("metadata", {})
                config = data.get("configuration", {})
                return {
                    "name": meta.get("name") or data.get("name", "Untitled Workflow"),
                    "description": meta.get("description") or data.get("description"),
                    "version": meta.get("version", "1.0.0"),
                    "status": data.get("status", "active"),
                    "tags": meta.get("tags", []),
                    "owner_id": meta.get("ownerId") or data.get("owner_id", "default-owner"),
                    "configuration": config,
                    "nodes": data.get("nodes", []),
                    "edges": data.get("edges", []),
                    "workflow_json": data,
                }
        return data


class WorkflowUpdate(BaseModel):
    """Schema for updating an existing workflow."""

    name: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = None
    status: Optional[str] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None
    workflow_json: Optional[Dict[str, Any]] = None
    configuration: Optional[WorkflowConfigurationSchema] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None
    change_summary: Optional[str] = None

    # Stale revision concurrency check
    base_revision_id: Optional[str] = Field(None, description="Current revision ID before this update")
    base_revision_number: Optional[int] = Field(None, description="Current revision number before this update")


class WorkflowRead(WorkflowBase):
    """Schema for workflow responses."""

    id: str
    owner_id: str = "default-owner"
    active_revision_id: Optional[str] = None
    current_revision_number: int = 1
    status: str = "active"
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def sync_workflow_json(self) -> "WorkflowRead":
        """Ensure workflow_json is populated with canonical structure if absent."""
        if not self.workflow_json:
            self.workflow_json = {
                "schemaVersion": "1.0.0",
                "metadata": {
                    "id": self.id,
                    "name": self.name,
                    "description": self.description or "",
                    "version": self.version,
                    "tags": self.tags,
                    "author": self.owner_id or "AgentForge AI",
                    "ownerId": self.owner_id,
                    "activeRevisionId": self.active_revision_id,
                    "currentRevisionNumber": self.current_revision_number,
                    "createdAt": self.created_at.isoformat(),
                    "updatedAt": self.updated_at.isoformat(),
                },
                "configuration": self.configuration.model_dump()
                if hasattr(self.configuration, "model_dump")
                else dict(self.configuration),
                "nodes": self.nodes,
                "edges": self.edges,
            }
        return self


# -----------------------------------------------------------------------------
# REVISION SCHEMAS (Phase 4)
# -----------------------------------------------------------------------------

class WorkflowRevisionRead(BaseModel):
    id: str
    workflow_id: str
    revision_number: int
    version: str
    snapshot: Dict[str, Any]
    change_summary: Optional[str] = None
    created_by: str
    is_active: bool
    is_verified: bool
    last_execution_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowRevisionDiffResponse(BaseModel):
    workflow_id: str
    source_revision_id: str
    target_revision_id: str
    source_revision_number: int
    target_revision_number: int
    nodes_added: List[Dict[str, Any]] = Field(default_factory=list)
    nodes_removed: List[Dict[str, Any]] = Field(default_factory=list)
    nodes_modified: List[Dict[str, Any]] = Field(default_factory=list)
    edges_added: List[Dict[str, Any]] = Field(default_factory=list)
    edges_removed: List[Dict[str, Any]] = Field(default_factory=list)
    edges_modified: List[Dict[str, Any]] = Field(default_factory=list)
    configuration_changes: Dict[str, Any] = Field(default_factory=dict)


class WorkflowRevisionPromoteRequest(BaseModel):
    execution_id: Optional[str] = Field(None, description="ID of successful execution validating this revision")


class WorkflowRevisionRestoreRequest(BaseModel):
    change_summary: Optional[str] = Field(None, description="Optional reason or description for restoring revision")


# -----------------------------------------------------------------------------
# RECOVERY SCHEMAS (Phase 5)
# -----------------------------------------------------------------------------

class WorkflowRecoveryReserveRequest(BaseModel):
    execution_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    error_context: Optional[Dict[str, Any]] = None


class WorkflowRecoveryCompleteRequest(BaseModel):
    status: str = Field(..., pattern="^(completed|failed|cancelled|resolved)$")
    proposed_patch: Optional[Dict[str, Any]] = None


class WorkflowRecoveryRead(BaseModel):
    id: str
    workflow_id: str
    revision_id: Optional[str] = None
    execution_id: Optional[str] = None
    attempt_number: int
    status: str
    idempotency_key: Optional[str] = None
    error_context: Optional[Dict[str, Any]] = None
    proposed_patch: Optional[Dict[str, Any]] = None
    reserved_at: datetime
    completed_at: Optional[datetime] = None
    promoted_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# VALIDATION SCHEMAS
# -----------------------------------------------------------------------------

class WorkflowValidateRequest(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)


class WorkflowValidateResponse(BaseModel):
    is_valid: bool
    readiness_score: int
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


# -----------------------------------------------------------------------------
# EXECUTION & TELEMETRY SCHEMAS (Phase 6)
# -----------------------------------------------------------------------------

class WorkflowExecutionCreate(BaseModel):
    workflow_id: Optional[str] = None
    revision_id: Optional[str] = None
    status: str = Field(default="pending", pattern="^(pending|running|completed|failed|repaired|PENDING|RUNNING|COMPLETED|FAILED|REPAIRED)$")
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    input_payload: Optional[Dict[str, Any]] = None  # backward compatibility
    output_result: Optional[Dict[str, Any]] = None  # backward compatibility
    error_message: Optional[str] = None
    execution_duration: Optional[float] = None
    repair_attempts: int = 0

    # Telemetry parameters
    node_logs: Optional[List[Dict[str, Any]]] = None
    token_usage: Optional[Dict[str, Any]] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    estimated_cost: Optional[float] = None
    reliability_report: Optional[Dict[str, Any]] = None
    repair_report: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def harmonize_inputs(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Sync input_data and input_payload
            if "input_payload" in data and "input_data" not in data:
                data["input_data"] = data["input_payload"]
            elif "input_data" in data and "input_payload" not in data:
                data["input_payload"] = data["input_data"]

            # Sync output_data and output_result
            if "output_result" in data and "output_data" not in data:
                data["output_data"] = data["output_result"]
            elif "output_data" in data and "output_result" not in data:
                data["output_result"] = data["output_data"]
        return data


class WorkflowExecutionUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|running|completed|failed|repaired|PENDING|RUNNING|COMPLETED|FAILED|REPAIRED)$")
    output_data: Optional[Dict[str, Any]] = None
    output_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_duration: Optional[float] = None
    repair_attempts: Optional[int] = None
    completed_at: Optional[datetime] = None

    # Telemetry updates
    node_logs: Optional[List[Dict[str, Any]]] = None
    token_usage: Optional[Dict[str, Any]] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    estimated_cost: Optional[float] = None
    reliability_report: Optional[Dict[str, Any]] = None
    repair_report: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def harmonize_outputs(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "output_result" in data and "output_data" not in data:
                data["output_data"] = data["output_result"]
            elif "output_data" in data and "output_result" not in data:
                data["output_result"] = data["output_data"]
        return data


class WorkflowExecutionRead(BaseModel):
    id: str
    workflow_id: str
    revision_id: Optional[str] = None
    status: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    input_payload: Optional[Dict[str, Any]] = None
    output_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_duration: Optional[float] = None
    repair_attempts: int
    started_at: datetime
    completed_at: Optional[datetime] = None

    # Telemetry fields
    node_logs: Optional[List[Dict[str, Any]]] = None
    token_usage: Optional[Dict[str, Any]] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    estimated_cost: Optional[float] = None
    reliability_report: Optional[Dict[str, Any]] = None
    repair_report: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def sync_payload_fields(self) -> "WorkflowExecutionRead":
        if self.input_payload is None and self.input_data is not None:
            self.input_payload = self.input_data
        if self.input_data is None and self.input_payload is not None:
            self.input_data = self.input_payload

        if self.output_result is None and self.output_data is not None:
            self.output_result = self.output_data
        if self.output_data is None and self.output_result is not None:
            self.output_data = self.output_result

        return self
