from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set
from app.schemas.execution import ExecutionStatus, TokenUsage, NodeExecutionLog


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutionEngineError(Exception):
    """Base exception for workflow execution engine."""
    def __init__(self, message: str, node_id: Optional[str] = None, stage: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.node_id = node_id
        self.stage = stage or "execution"


class WorkflowValidationError(ExecutionEngineError):
    """Raised when workflow structure or parameters fail validation."""
    def __init__(self, message: str, node_id: Optional[str] = None):
        super().__init__(message, node_id=node_id, stage="validation")


class CycleDetectedError(WorkflowValidationError):
    """Raised when cyclic dependencies are detected in a directed workflow."""
    pass


class NodeExecutionError(ExecutionEngineError):
    """Raised when an individual node execution fails."""
    pass


class MissingInputError(WorkflowValidationError):
    """Raised when required input for a workflow or node is missing."""
    pass


class UnsupportedNodeTypeError(WorkflowValidationError):
    """Raised when encountering an unhandled or unsupported node type."""
    pass


class ToolExecutionError(NodeExecutionError):
    """Raised when a predefined tool fails or is unauthorized."""
    pass


class GeminiConfigError(NodeExecutionError):
    """Raised when Gemini API key or model configuration is missing."""
    pass


class HumanApprovalRequired(Exception):
    """Raised to pause execution when a human approval gate is reached."""
    def __init__(self, node_id: str, message: str = "Awaiting human sign-off"):
        super().__init__(message)
        self.node_id = node_id
        self.message = message


@dataclass
class ExecutionContext:
    """Shared execution context passed through the workflow runner."""
    workflow_id: Optional[str]
    execution_id: str
    workflow_version: str = "1.0.0"
    inputs: Dict[str, Any] = field(default_factory=dict)
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    node_states: Dict[str, ExecutionStatus] = field(default_factory=dict)
    node_durations: Dict[str, float] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    logs: List[NodeExecutionLog] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)
    waiting_node_id: Optional[str] = None
    failed_node_id: Optional[str] = None
    total_api_calls: int = 0
    total_token_usage: TokenUsage = field(default_factory=TokenUsage)
    completed_nodes: Set[str] = field(default_factory=set)
    skipped_nodes: Set[str] = field(default_factory=set)
    start_time: str = field(default_factory=utc_now_iso)
    end_time: Optional[str] = None
    total_duration_ms: float = 0.0
    status: ExecutionStatus = ExecutionStatus.PENDING

    def record_node_log(self, log: NodeExecutionLog) -> None:
        # Replace or append log for node
        for i, existing in enumerate(self.logs):
            if existing.node_id == log.node_id:
                self.logs[i] = log
                return
        self.logs.append(log)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "workflow_version": self.workflow_version,
            "inputs": self.inputs,
            "node_outputs": self.node_outputs,
            "node_states": {k: v.value for k, v in self.node_states.items()},
            "node_durations": self.node_durations,
            "variables": self.variables,
            "logs": [log.model_dump() for log in self.logs],
            "errors": self.errors,
            "waiting_node_id": self.waiting_node_id,
            "failed_node_id": self.failed_node_id,
            "total_api_calls": self.total_api_calls,
            "total_token_usage": self.total_token_usage.model_dump(),
            "completed_nodes": list(self.completed_nodes),
            "skipped_nodes": list(self.skipped_nodes),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration_ms": self.total_duration_ms,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionContext":
        ctx = cls(
            workflow_id=data.get("workflow_id"),
            execution_id=data["execution_id"],
            workflow_version=data.get("workflow_version", "1.0.0"),
            inputs=data.get("inputs", {}),
            node_outputs=data.get("node_outputs", {}),
            node_states={k: ExecutionStatus(v) for k, v in data.get("node_states", {}).items()},
            node_durations=data.get("node_durations", {}),
            variables=data.get("variables", {}),
            logs=[NodeExecutionLog(**item) for item in data.get("logs", [])],
            errors=data.get("errors", {}),
            waiting_node_id=data.get("waiting_node_id"),
            failed_node_id=data.get("failed_node_id"),
            total_api_calls=data.get("total_api_calls", 0),
            total_token_usage=TokenUsage(**data.get("total_token_usage", {})),
            completed_nodes=set(data.get("completed_nodes", [])),
            skipped_nodes=set(data.get("skipped_nodes", [])),
            start_time=data.get("start_time", utc_now_iso()),
            end_time=data.get("end_time"),
            total_duration_ms=data.get("total_duration_ms", 0.0),
            status=ExecutionStatus(data.get("status", ExecutionStatus.PENDING.value)),
        )
        return ctx
