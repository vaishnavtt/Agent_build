from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class NodeExecutionLog(BaseModel):
    node_id: str
    node_name: str = ""
    node_type: str
    status: ExecutionStatus
    start_time: str
    end_time: Optional[str] = None
    duration_ms: float = 0.0
    input_summary: Optional[Dict[str, Any]] = None
    output_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    api_call_count: int = 0
    token_usage: Optional[TokenUsage] = None


class ExecutionMetrics(BaseModel):
    execution_id: str
    workflow_id: Optional[str] = None
    total_duration_ms: float = 0.0
    node_durations_ms: Dict[str, float] = Field(default_factory=dict)
    total_api_calls: int = 0
    total_token_usage: Optional[TokenUsage] = None
    nodes_executed: int = 0
    nodes_skipped: int = 0
    nodes_failed: int = 0
    failed_node_id: Optional[str] = None
    reexecution_overhead_ms: Optional[float] = None


class WorkflowExecuteRequest(BaseModel):
    inputs: Dict[str, Any] = Field(default_factory=dict)
    version: Optional[str] = "1.0.0"


class ApprovalActionRequest(BaseModel):
    comment: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ExecutionReportResponse(BaseModel):
    execution_id: str
    workflow_id: Optional[str] = None
    workflow_version: str = "1.0.0"
    status: ExecutionStatus
    start_time: str
    end_time: Optional[str] = None
    total_duration_ms: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    failed_node_id: Optional[str] = None
    waiting_node_id: Optional[str] = None
    node_logs: List[NodeExecutionLog] = Field(default_factory=list)
    metrics: ExecutionMetrics
