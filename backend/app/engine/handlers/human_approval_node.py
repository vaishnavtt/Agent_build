from typing import Dict, Any
from app.engine.handlers.base import BaseNodeHandler
from app.engine.types import ExecutionContext, HumanApprovalRequired, NodeExecutionError


class HumanApprovalNodeHandler(BaseNodeHandler):
    """Pauses workflow execution until an external human approval action is recorded."""

    def __init__(self):
        super().__init__("Human Approval")

    async def execute(
        self,
        node: Dict[str, Any],
        incoming_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        node_id = node.get("id", "")
        node_name = node.get("name", "Human Approval")

        approved_nodes = context.variables.get("_approved_nodes", {})
        rejected_nodes = context.variables.get("_rejected_nodes", {})

        # Check if this node has been explicitly approved
        if node_id in approved_nodes:
            approval_info = approved_nodes[node_id]
            return {
                "status": "APPROVED",
                "approved": True,
                "approver_comment": approval_info.get("comment", ""),
                "approved_data": approval_info.get("data", incoming_data),
                "output": incoming_data,
            }

        # Check if this node has been explicitly rejected
        if node_id in rejected_nodes:
            reject_info = rejected_nodes[node_id]
            reason = reject_info.get("comment", "Human approver rejected the execution.")
            raise NodeExecutionError(
                f"Human approval denied on node '{node_name}': {reason}",
                node_id=node_id,
            )

        # Neither approved nor rejected yet: pause execution
        prompt_message = node.get("config", {}).get(
            "prompt", f"Sign-off required for workflow step '{node_name}'."
        )
        raise HumanApprovalRequired(node_id=node_id, message=prompt_message)
