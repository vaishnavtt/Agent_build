from typing import Dict, Any
from app.engine.handlers.base import BaseNodeHandler
from app.engine.types import ExecutionContext, ToolExecutionError
from app.engine.tool_registry import tool_registry


class ToolNodeHandler(BaseNodeHandler):
    """Handler invoking approved, predefined tools from the tool registry."""

    def __init__(self):
        super().__init__("Tool")

    async def execute(
        self,
        node: Dict[str, Any],
        incoming_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        config = node.get("config", {})
        node_id = node.get("id", "")
        node_name = node.get("name", "Tool Node")

        tool_name = config.get("toolName") or config.get("tool") or "web_search"
        tool_name = str(tool_name).strip()

        if not tool_registry.has_tool(tool_name):
            available = ", ".join(t["name"] for t in tool_registry.list_tools())
            raise ToolExecutionError(
                f"Unauthorized or unknown tool '{tool_name}' on node '{node_name}'. "
                f"Allowed registered tools: {available}",
                node_id=node_id,
            )

        tool_meta = tool_registry.get_tool(tool_name)
        handler_fn = tool_meta["handler"]

        # Merge config parameters with incoming data
        merged_params = {}
        merged_params.update(config)
        merged_params.update(incoming_data)

        try:
            result = await handler_fn(merged_params, context)
        except ToolExecutionError:
            raise
        except Exception as e:
            raise ToolExecutionError(
                f"Execution failed for tool '{tool_name}' on node '{node_name}': {str(e)}",
                node_id=node_id,
            )

        return {
            "result": result,
            "output": result,
            "tool": tool_name,
            "status": "success",
        }
