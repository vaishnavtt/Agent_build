from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.engine.types import ExecutionContext, NodeExecutionError
from app.schemas.execution import TokenUsage


class BaseNodeHandler(ABC):
    """Abstract base class for all node execution handlers."""

    def __init__(self, node_type: str):
        self.node_type = node_type
        self.api_calls_made: int = 0
        self.token_usage: Optional[TokenUsage] = None

    @abstractmethod
    async def execute(
        self,
        node: Dict[str, Any],
        incoming_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute the node logic and return output dictionary."""
        pass
