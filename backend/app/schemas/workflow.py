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
    type: NodeType
    name: str
    position: NodePosition
    config: Dict[str, Any] = Field(default_factory=dict)
    inputHandles: Optional[List[str]] = Field(default_factory=list)
    outputHandles: Optional[List[str]] = Field(default_factory=list)


class WorkflowEdgeSchema(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    condition: Optional[str] = None


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
    nodes: List[WorkflowNodeSchema] = Field(default_factory=list)
    edges: List[WorkflowEdgeSchema] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowRead(WorkflowBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

