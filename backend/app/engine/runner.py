import uuid
import time
from typing import Dict, Any, List, Optional, Set
from app.engine.types import (
    ExecutionContext,
    ExecutionEngineError,
    WorkflowValidationError,
    HumanApprovalRequired,
    utc_now_iso,
)
from app.engine.graph import WorkflowGraph
from app.engine.handlers import get_handler_for_node
from app.engine.performance import ExecutionPerformanceMonitor
from app.schemas.execution import (
    ExecutionStatus,
    NodeExecutionLog,
    ExecutionReportResponse,
)


class WorkflowExecutionEngine:
    """Modular 10-stage workflow execution engine orchestrating node traversal,
    data passing, branching, pause/resume, and performance monitoring.
    """

    def __init__(self):
        self.active_contexts: Dict[str, ExecutionContext] = {}

    def get_context(self, execution_id: str) -> Optional[ExecutionContext]:
        return self.active_contexts.get(execution_id)

    def set_context(self, execution_id: str, context: ExecutionContext) -> None:
        self.active_contexts[execution_id] = context

    async def execute(
        self,
        workflow: Dict[str, Any],
        inputs: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None,
        context: Optional[ExecutionContext] = None,
        reexecution: bool = False,
        original_duration_ms: Optional[float] = None,
    ) -> ExecutionReportResponse:
        """Executes a workflow directed graph end-to-end."""
        # Stage 1: Receive workflow JSON and execution input
        exec_id = execution_id or str(uuid.uuid4())
        workflow_id = workflow.get("id") or workflow.get("metadata", {}).get("id")
        workflow_version = (
            workflow.get("version")
            or workflow.get("metadata", {}).get("version")
            or "1.0.0"
        )
        input_data = inputs or {}

        # Stage 2: Validate the basic workflow structure and required execution info
        raw_nodes = workflow.get("nodes")
        raw_edges = workflow.get("edges", [])

        if not isinstance(raw_nodes, list) or len(raw_nodes) == 0:
            raise WorkflowValidationError("Workflow must contain a non-empty list of nodes.")

        # Stage 3: Build execution graph
        graph = WorkflowGraph(raw_nodes, raw_edges)

        # Stage 4: Determine execution order using topological sorting & cycle detection
        execution_order = graph.get_topological_order()

        # Initialize or reuse execution context & performance monitor
        if context is None:
            context = ExecutionContext(
                workflow_id=workflow_id,
                execution_id=exec_id,
                workflow_version=workflow_version,
                inputs=input_data,
                status=ExecutionStatus.RUNNING,
            )
        else:
            context.status = ExecutionStatus.RUNNING

        self.active_contexts[exec_id] = context

        perf_monitor = ExecutionPerformanceMonitor(
            execution_id=exec_id, workflow_id=workflow_id
        )

        final_output: Optional[Dict[str, Any]] = None
        skipped_nodes: Set[str] = set(context.skipped_nodes)

        # Stage 5 through 9: Node execution, data transfer, branching, logging
        try:
            for node_id in execution_order:
                # If resuming and node already completed, skip re-running
                if node_id in context.completed_nodes:
                    continue

                node = graph.nodes[node_id]
                node_name = node.get("name", node_id)
                node_type = node.get("type", "Unknown")

                # If node was marked skipped by an upstream conditional branch
                if node_id in skipped_nodes:
                    context.skipped_nodes.add(node_id)
                    context.node_states[node_id] = ExecutionStatus.SKIPPED
                    perf_monitor.end_node(node_id, ExecutionStatus.SKIPPED)

                    skipped_log = NodeExecutionLog(
                        node_id=node_id,
                        node_name=node_name,
                        node_type=node_type,
                        status=ExecutionStatus.SKIPPED,
                        start_time=utc_now_iso(),
                        end_time=utc_now_iso(),
                        duration_ms=0.0,
                    )
                    context.record_node_log(skipped_log)
                    continue

                # Stage 6: Transfer output data from connected upstream nodes
                incoming_data = graph.get_incoming_data(node_id, context.node_outputs)

                # Stage 8: Track execution timing for each node
                node_start_iso = utc_now_iso()
                perf_monitor.start_node(node_id)
                context.node_states[node_id] = ExecutionStatus.RUNNING

                try:
                    # Retrieve appropriate node handler
                    handler = get_handler_for_node(node_type)

                    # Stage 5: Execute node using its handler
                    node_output = await handler.execute(node, incoming_data, context)

                    # Successful completion
                    duration_ms = perf_monitor.end_node(
                        node_id,
                        ExecutionStatus.SUCCESS,
                        api_calls=handler.api_calls_made,
                        token_usage=handler.token_usage,
                    )

                    context.node_outputs[node_id] = node_output
                    context.node_states[node_id] = ExecutionStatus.SUCCESS
                    context.completed_nodes.add(node_id)
                    context.total_api_calls += handler.api_calls_made
                    if handler.token_usage:
                        context.total_token_usage.prompt_tokens += handler.token_usage.prompt_tokens
                        context.total_token_usage.completion_tokens += handler.token_usage.completion_tokens
                        context.total_token_usage.total_tokens += handler.token_usage.total_tokens

                    # Stage 7: Conditional branching evaluation
                    if node_type == "Condition" or node_type.lower() == "condition":
                        branch_taken = node_output.get("branch", "true")
                        new_skipped = graph.determine_skipped_nodes_for_condition(
                            node_id, branch_taken
                        )
                        skipped_nodes.update(new_skipped)
                        context.skipped_nodes.update(new_skipped)

                    if node_type in ("Output", "output"):
                        final_output = node_output

                    # Stage 9: Capture node execution logs
                    node_log = NodeExecutionLog(
                        node_id=node_id,
                        node_name=node_name,
                        node_type=node_type,
                        status=ExecutionStatus.SUCCESS,
                        start_time=node_start_iso,
                        end_time=utc_now_iso(),
                        duration_ms=duration_ms,
                        input_summary=self._safe_summary(incoming_data),
                        output_summary=self._safe_summary(node_output),
                        api_call_count=handler.api_calls_made,
                        token_usage=handler.token_usage,
                    )
                    context.record_node_log(node_log)

                except HumanApprovalRequired as har:
                    # Pause execution at Human Approval Gate
                    duration_ms = perf_monitor.end_node(
                        node_id, ExecutionStatus.WAITING_FOR_APPROVAL
                    )
                    context.status = ExecutionStatus.WAITING_FOR_APPROVAL
                    context.waiting_node_id = node_id
                    context.node_states[node_id] = ExecutionStatus.WAITING_FOR_APPROVAL

                    waiting_log = NodeExecutionLog(
                        node_id=node_id,
                        node_name=node_name,
                        node_type=node_type,
                        status=ExecutionStatus.WAITING_FOR_APPROVAL,
                        start_time=node_start_iso,
                        end_time=utc_now_iso(),
                        duration_ms=duration_ms,
                        input_summary=self._safe_summary(incoming_data),
                        error_message=har.message,
                    )
                    context.record_node_log(waiting_log)

                    metrics = perf_monitor.finish()
                    return ExecutionReportResponse(
                        execution_id=exec_id,
                        workflow_id=workflow_id,
                        workflow_version=workflow_version,
                        status=ExecutionStatus.WAITING_FOR_APPROVAL,
                        start_time=context.start_time,
                        end_time=None,
                        total_duration_ms=metrics.total_duration_ms,
                        waiting_node_id=node_id,
                        node_logs=context.logs,
                        metrics=metrics,
                    )

                except Exception as ne:
                    # Handle node execution failure
                    duration_ms = perf_monitor.end_node(node_id, ExecutionStatus.FAILED)
                    err_msg = str(ne)
                    context.status = ExecutionStatus.FAILED
                    context.failed_node_id = node_id
                    context.errors[node_id] = err_msg
                    context.node_states[node_id] = ExecutionStatus.FAILED

                    failed_log = NodeExecutionLog(
                        node_id=node_id,
                        node_name=node_name,
                        node_type=node_type,
                        status=ExecutionStatus.FAILED,
                        start_time=node_start_iso,
                        end_time=utc_now_iso(),
                        duration_ms=duration_ms,
                        input_summary=self._safe_summary(incoming_data),
                        error_message=err_msg,
                    )
                    context.record_node_log(failed_log)

                    # Mark subsequent pending nodes as skipped
                    curr_idx = execution_order.index(node_id)
                    for remaining_id in execution_order[curr_idx + 1 :]:
                        r_node = graph.nodes[remaining_id]
                        context.node_states[remaining_id] = ExecutionStatus.SKIPPED
                        rem_log = NodeExecutionLog(
                            node_id=remaining_id,
                            node_name=r_node.get("name", remaining_id),
                            node_type=r_node.get("type", "Unknown"),
                            status=ExecutionStatus.SKIPPED,
                            start_time=utc_now_iso(),
                            end_time=utc_now_iso(),
                            duration_ms=0.0,
                        )
                        context.record_node_log(rem_log)

                    metrics = perf_monitor.finish()
                    return ExecutionReportResponse(
                        execution_id=exec_id,
                        workflow_id=workflow_id,
                        workflow_version=workflow_version,
                        status=ExecutionStatus.FAILED,
                        start_time=context.start_time,
                        end_time=utc_now_iso(),
                        total_duration_ms=metrics.total_duration_ms,
                        error_message=err_msg,
                        failed_node_id=node_id,
                        node_logs=context.logs,
                        metrics=metrics,
                    )

            # Execution completed all nodes successfully
            context.status = ExecutionStatus.SUCCESS
            context.end_time = utc_now_iso()

            if reexecution and original_duration_ms:
                # Calculate repair execution overhead
                overhead = max(0.0, perf_monitor._start_perf - original_duration_ms)
                perf_monitor.record_reexecution_overhead(overhead)

            metrics = perf_monitor.finish()

            # Stage 10: Return structured execution report
            return ExecutionReportResponse(
                execution_id=exec_id,
                workflow_id=workflow_id,
                workflow_version=workflow_version,
                status=ExecutionStatus.SUCCESS,
                start_time=context.start_time,
                end_time=context.end_time,
                total_duration_ms=metrics.total_duration_ms,
                result=final_output or context.node_outputs,
                node_logs=context.logs,
                metrics=metrics,
            )

        except Exception as e:
            if isinstance(e, ExecutionEngineError):
                raise
            raise ExecutionEngineError(f"Unexpected execution engine failure: {str(e)}")

    async def resume_after_approval(
        self,
        workflow: Dict[str, Any],
        context: ExecutionContext,
        action: str,  # "approve" or "reject"
        comment: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> ExecutionReportResponse:
        """Resumes a paused workflow execution following a human approval or rejection."""
        waiting_node_id = context.waiting_node_id
        if not waiting_node_id:
            raise WorkflowValidationError("No waiting human approval step found in context.")

        if action.lower() == "reject":
            # Approver rejected the execution
            reject_reason = f"Execution rejected: {comment}" if comment else "Execution rejected by human approver."
            context.variables.setdefault("_rejected_nodes", {})[waiting_node_id] = {
                "comment": reject_reason,
                "data": data,
            }
            context.status = ExecutionStatus.REJECTED
            context.end_time = utc_now_iso()

            # Update waiting node log
            for log in context.logs:
                if log.node_id == waiting_node_id:
                    log.status = ExecutionStatus.REJECTED
                    log.error_message = reject_reason

            metrics = ExecutionPerformanceMonitor(
                context.execution_id, context.workflow_id
            ).finish()

            return ExecutionReportResponse(
                execution_id=context.execution_id,
                workflow_id=context.workflow_id,
                workflow_version=context.workflow_version,
                status=ExecutionStatus.REJECTED,
                start_time=context.start_time,
                end_time=context.end_time,
                total_duration_ms=context.total_duration_ms,
                error_message=reject_reason,
                failed_node_id=waiting_node_id,
                node_logs=context.logs,
                metrics=metrics,
            )

        # Action is approve: record approval and resume execution from waiting node
        context.variables.setdefault("_approved_nodes", {})[waiting_node_id] = {
            "comment": comment or "Approved by human approver",
            "data": data,
        }
        context.waiting_node_id = None

        return await self.execute(
            workflow=workflow,
            inputs=context.inputs,
            execution_id=context.execution_id,
            context=context,
        )

    def _safe_summary(self, data: Any) -> Dict[str, Any]:
        """Sanitizes summaries to avoid storing massive buffers or secret keys in logs."""
        if not isinstance(data, dict):
            return {"value": str(data)[:300]}

        sanitized = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(secret in k_lower for secret in ("key", "secret", "token", "password")):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, (str, bytes)):
                sanitized[k] = str(v)[:300] + ("..." if len(str(v)) > 300 else "")
            elif isinstance(v, (int, float, bool)):
                sanitized[k] = v
            elif isinstance(v, dict):
                sanitized[k] = f"dict({len(v)} keys)"
            elif isinstance(v, list):
                sanitized[k] = f"list({len(v)} items)"
            else:
                sanitized[k] = str(v)[:200]
        return sanitized


# Global execution engine instance
execution_engine = WorkflowExecutionEngine()
