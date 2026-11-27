from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

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
    version: str = "1.0.0"
    configuration: WorkflowConfigurationSchema = Field(default_factory=WorkflowConfigurationSchema)
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    configuration: Optional[WorkflowConfigurationSchema] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None


class WorkflowRead(WorkflowBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowValidateRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class WorkflowValidateResponse(BaseModel):
    is_valid: bool
    readiness_score: int
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionCreate(BaseModel):
    workflow_id: str
    status: str = "COMPLETED"
    input_payload: Optional[Dict[str, Any]] = None
    output_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    repair_attempts: int = 0


class WorkflowExecutionRead(BaseModel):
    id: str
    workflow_id: str
    workflow_revision_id: Optional[str] = None
    status: str
    input_payload: Optional[Dict[str, Any]] = None
    output_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    failed_node_id: Optional[str] = None
    repair_attempts: int
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
