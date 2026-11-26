from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    """Structured execution contract returned by Member 4's workflow execution engine."""

    status: Literal["COMPLETED", "FAILED", "TIMEOUT", "SAFE_REJECTION"]
    output_data: Optional[Dict[str, Any]] = None
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    duration_ms: Optional[float] = None


class IWorkflowExecutor(ABC):
    """Abstract adapter decoupling Member 5's Reliability Lab from Member 4's execution engine."""

    @abstractmethod
    async def execute(
        self,
        workflow_id: str,
        input_payload: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute a workflow with the given input payload and return structured results."""
        raise NotImplementedError
