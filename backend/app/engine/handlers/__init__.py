from typing import Dict, Type
from app.engine.handlers.base import BaseNodeHandler
from app.engine.handlers.input_node import InputNodeHandler
from app.engine.handlers.llm_node import LLMNodeHandler
from app.engine.handlers.document_reader import DocumentReaderNodeHandler
from app.engine.handlers.tool_node import ToolNodeHandler
from app.engine.handlers.condition_node import ConditionNodeHandler
from app.engine.handlers.human_approval_node import HumanApprovalNodeHandler
from app.engine.handlers.output_node import OutputNodeHandler
from app.engine.types import UnsupportedNodeTypeError

# Registry mapping node type strings to their respective handler classes
_HANDLER_REGISTRY: Dict[str, Type[BaseNodeHandler]] = {
    # Canonical names
    "Input": InputNodeHandler,
    "LLM": LLMNodeHandler,
    "Document Reader": DocumentReaderNodeHandler,
    "Tool": ToolNodeHandler,
    "Condition": ConditionNodeHandler,
    "Human Approval": HumanApprovalNodeHandler,
    "Output": OutputNodeHandler,
    # Aliases
    "PDF Document Reader": DocumentReaderNodeHandler,
    "PDF Reader": DocumentReaderNodeHandler,
    "Predefined Tool": ToolNodeHandler,
    # Lowercase aliases
    "input": InputNodeHandler,
    "llm": LLMNodeHandler,
    "document reader": DocumentReaderNodeHandler,
    "tool": ToolNodeHandler,
    "condition": ConditionNodeHandler,
    "human approval": HumanApprovalNodeHandler,
    "output": OutputNodeHandler,
}


def get_handler_for_node(node_type: str) -> BaseNodeHandler:
    """Retrieves an instantiated handler for a given node type."""
    handler_cls = _HANDLER_REGISTRY.get(node_type.strip())
    if not handler_cls:
        supported = ", ".join(
            sorted(
                set(
                    [
                        "Input",
                        "LLM",
                        "Document Reader",
                        "Tool",
                        "Condition",
                        "Human Approval",
                        "Output",
                    ]
                )
            )
        )
        raise UnsupportedNodeTypeError(
            f"Unsupported node type '{node_type}'. Supported types: {supported}"
        )
    return handler_cls()


__all__ = [
    "BaseNodeHandler",
    "InputNodeHandler",
    "LLMNodeHandler",
    "DocumentReaderNodeHandler",
    "ToolNodeHandler",
    "ConditionNodeHandler",
    "HumanApprovalNodeHandler",
    "OutputNodeHandler",
    "get_handler_for_node",
]
