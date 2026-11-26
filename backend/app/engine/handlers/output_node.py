import json
from typing import Dict, Any
from app.engine.handlers.base import BaseNodeHandler
from app.engine.types import ExecutionContext


class OutputNodeHandler(BaseNodeHandler):
    """Terminal node collecting, formatting, and presenting final workflow results."""

    def __init__(self):
        super().__init__("Output")

    async def execute(
        self,
        node: Dict[str, Any],
        incoming_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        config = node.get("config", {})
        output_format = config.get("outputFormat", "json").lower()

        primary_result = (
            incoming_data.get("output")
            or incoming_data.get("response")
            or incoming_data.get("result")
            or incoming_data.get("text")
            or incoming_data
        )

        formatted_result: Any
        if output_format == "text":
            formatted_result = str(primary_result)
        elif output_format == "markdown":
            formatted_result = f"### Workflow Result\n\n{primary_result}"
        else:
            # json or dictionary
            formatted_result = primary_result

        return {
            "result": formatted_result,
            "format": output_format,
            "raw": incoming_data,
            "status": "COMPLETED",
        }
