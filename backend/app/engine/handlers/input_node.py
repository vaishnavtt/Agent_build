import json
from typing import Dict, Any
from app.engine.handlers.base import BaseNodeHandler, get_node_meta
from app.engine.types import ExecutionContext, MissingInputError, WorkflowValidationError


class InputNodeHandler(BaseNodeHandler):
    """Handler for workflow entry points ingesting and validating parameters and payloads."""

    def __init__(self):
        super().__init__("Input")

    async def execute(
        self,
        node: Dict[str, Any],
        incoming_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        node_id, node_name, config = get_node_meta(node, "Input")
        required = config.get("required", True)
        default_val = config.get("defaultValue", "")
        input_type = str(config.get("inputType", "text")).lower().strip()

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
        elif isinstance(context.inputs, dict) and context.inputs and len(context.inputs) > 0:
            # Support multi-key dict inputs when no node-specific key is used
            if not any(k in context.inputs for k in (node_id, node_name)):
                val = context.inputs
        elif context.inputs and not isinstance(context.inputs, dict):
            val = context.inputs
        elif incoming_data:
            val = incoming_data

        if val is None or val == "":
            if default_val not in (None, ""):
                val = default_val
            elif required:
                raise MissingInputError(
                    f"Missing required input for node '{node_name or node_id}'.",
                    node_id=node_id,
                )
            else:
                val = ""

        # Validate inputType when configured
        if input_type == "json" and isinstance(val, str) and val.strip():
            try:
                val = json.loads(val)
            except json.JSONDecodeError as exc:
                raise WorkflowValidationError(
                    f"Invalid JSON input for node '{node_name or node_id}': {exc}",
                    node_id=node_id,
                )

        # Update context variables
        context.variables[node_id] = val
        if node_name:
            context.variables[node_name] = val

        result: Dict[str, Any] = {
            "output": val,
            "data": val,
            "text": str(val) if not isinstance(val, (dict, list)) else val,
            "node_id": node_id,
        }
        if isinstance(val, dict):
            result.update(val)
        return result
