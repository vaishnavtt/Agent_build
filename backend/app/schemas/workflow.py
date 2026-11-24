from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, model_validator

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
    name: Optional[str] = Field(default=None, max_length=120)
    workflow_name: Optional[str] = Field(default=None, max_length=120)
    description: Optional[str] = None
    version: str = "1.0.0"
    configuration: WorkflowConfigurationSchema = Field(default_factory=WorkflowConfigurationSchema)
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    workflow_data: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def sync_name_and_data(self):
        # Sync name and workflow_name
        if not self.name and self.workflow_name:
            self.name = self.workflow_name
        elif not self.workflow_name and self.name:
            self.workflow_name = self.name
        elif not self.name and not self.workflow_name:
            self.name = "Untitled Workflow"
            self.workflow_name = "Untitled Workflow"

        # Sync workflow_data and nodes/edges
        if self.workflow_data and isinstance(self.workflow_data, dict):
            if not self.nodes:
                self.nodes = self.workflow_data.get("nodes", [])
            if not self.edges:
                self.edges = self.workflow_data.get("edges", [])
        elif not self.workflow_data:
            self.workflow_data = {
                "nodes": self.nodes,
                "edges": self.edges,
                "configuration": self.configuration.model_dump() if hasattr(self.configuration, "model_dump") else dict(self.configuration),
            }
        return self


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    workflow_name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    configuration: Optional[WorkflowConfigurationSchema] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    workflow_data: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

    @model_validator(mode="after")
    def sync_update_fields(self):
        if not self.name and self.workflow_name:
            self.name = self.workflow_name
        elif not self.workflow_name and self.name:
            self.workflow_name = self.name

        if self.workflow_data and isinstance(self.workflow_data, dict):
            if self.nodes is None:
                self.nodes = self.workflow_data.get("nodes")
            if self.edges is None:
                self.edges = self.workflow_data.get("edges")
        return self


class WorkflowRead(WorkflowBase):
    id: str
    name: str
    workflow_name: Optional[str] = None
    workflow_data: Optional[Dict[str, Any]] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def populate_read_aliases(self):
        if not self.workflow_name:
            self.workflow_name = self.name
        if not self.workflow_data:
            self.workflow_data = {
                "nodes": self.nodes,
                "edges": self.edges,
                "configuration": self.configuration.model_dump() if hasattr(self.configuration, "model_dump") else dict(self.configuration),
            }
        return self


class WorkflowValidateRequest(BaseModel):
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None


class WorkflowValidateResponse(BaseModel):
    is_valid: bool
    readiness_score: int
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionCreate(BaseModel):
    workflow_id: str
    workflow_name: Optional[str] = None
    status: str = "COMPLETED"
    execution_status: Optional[str] = None
    trigger_type: str = "MANUAL"
    input_payload: Optional[Dict[str, Any]] = None
    output_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    repair_attempts: int = 0
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    log_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    execution_logs: Optional[Any] = None
    repair_report: Optional[Dict[str, Any]] = None
    duration: Optional[str] = "0s"
    started_at: Optional[datetime] = None
    start_time: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @model_validator(mode="after")
    def sync_exec_fields(self):
        if not self.execution_status and self.status:
            self.execution_status = self.status.capitalize()
        elif not self.status and self.execution_status:
            self.status = self.execution_status.upper()

        if self.execution_logs is None and self.log_evidence:
            self.execution_logs = self.log_evidence
        elif self.log_evidence == [] and self.execution_logs:
            self.log_evidence = self.execution_logs if isinstance(self.execution_logs, list) else [self.execution_logs]

        if not self.start_time and self.started_at:
            self.start_time = self.started_at
        elif not self.started_at and self.start_time:
            self.started_at = self.start_time

        if not self.end_time and self.completed_at:
            self.end_time = self.completed_at
        elif not self.completed_at and self.end_time:
            self.completed_at = self.end_time
        return self


class WorkflowExecutionRead(BaseModel):
    id: str
    workflow_id: str
    workflow_name: Optional[str] = None
    status: str
    execution_status: Optional[str] = None
    trigger_type: str = "MANUAL"
    input_payload: Optional[Dict[str, Any]] = None
    output_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    repair_attempts: int = 0
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    log_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    execution_logs: Optional[Any] = None
    repair_report: Optional[Dict[str, Any]] = None
    duration: Optional[str] = "0s"
    started_at: datetime
    start_time: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    end_time: Optional[datetime] = None

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def populate_aliases(self):
        if not self.execution_status and self.status:
            self.execution_status = self.status.capitalize()
        if not self.start_time:
            self.start_time = self.started_at
        if not self.end_time and self.completed_at:
            self.end_time = self.completed_at
        if self.execution_logs is None and self.log_evidence:
            self.execution_logs = self.log_evidence
        return self
