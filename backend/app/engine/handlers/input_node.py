from typing import Dict, Any
from app.engine.handlers.base import BaseNodeHandler
from app.engine.types import ExecutionContext, MissingInputError


class InputNodeHandler(BaseNodeHandler):
    """Handler for workflow entry points ingesting parameters and payloads."""

    def __init__(self):
        super().__init__("Input")

    async def execute(
        self,
        node: Dict[str, Any],
        incoming_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        config = node.get("config", {})
        node_id = node.get("id", "")
        node_name = node.get("name", "")
        required = config.get("required", True)
        default_val = config.get("defaultValue", "")

        # Lookup in context inputs by node_id, node_name, or common keys
        val = None
        if node_id in context.inputs:
            val = context.inputs[node_id]
        elif node_name in context.inputs:
            val = context.inputs[node_name]
        elif "query" in context.inputs and len(context.inputs) == 1:
            val = context.inputs["query"]
        elif "input" in context.inputs and len(context.inputs) == 1:
            val = context.inputs["input"]
        elif "text" in context.inputs and len(context.inputs) == 1:
            val = context.inputs["text"]
        elif context.inputs and not isinstance(context.inputs, dict):
            val = context.inputs
        elif incoming_data:
            val = incoming_data

        if val is None or val == "":
            if default_val:
                val = default_val
            elif required:
                raise MissingInputError(
                    f"Missing required input for node '{node_name or node_id}'.",
                    node_id=node_id,
                )
            else:
                val = ""

        # Update context variables
        context.variables[node_id] = val
        if node_name:
            context.variables[node_name] = val

        result = {
            "output": val,
            "data": val,
            "text": str(val) if not isinstance(val, (dict, list)) else val,
            "node_id": node_id,
        }
        if isinstance(val, dict):
            result.update(val)
        return result
