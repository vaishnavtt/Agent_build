from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from app.engine.types import ExecutionContext, NodeExecutionError
from app.schemas.execution import TokenUsage


def get_node_meta(node: Dict[str, Any], default_name: str = "Node") -> Tuple[str, str, Dict[str, Any]]:
    """Extracts (node_id, node_name, config) supporting both canonical and React Flow node shapes."""
    data = node.get("data") if isinstance(node.get("data"), dict) else {}
    node_id = node.get("id", "")
    node_name = node.get("name") or data.get("label") or node_id or default_name
    config = node.get("config")
    if not isinstance(config, dict) or not config:
        config = data.get("config") if isinstance(data.get("config"), dict) else {}
    return node_id, node_name, config


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
