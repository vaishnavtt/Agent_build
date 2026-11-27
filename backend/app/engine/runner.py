import asyncio
import uuid
from typing import Dict, Any, Optional, Set, Tuple
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
from app.engine.security import redact_sensitive_data, redact_text
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
        candidate_mode: bool = False,
    ) -> ExecutionReportResponse:
        """Executes a workflow directed graph end-to-end."""
        exec_id = execution_id or str(uuid.uuid4())
        workflow_id = workflow.get("id") or workflow.get("metadata", {}).get("id")
        workflow_version = (
            workflow.get("version")
            or workflow.get("metadata", {}).get("version")
            or "1.0.0"
        )
        input_data = inputs or {}

        raw_nodes = workflow.get("nodes")
        raw_edges = workflow.get("edges", [])

        if not isinstance(raw_nodes, list) or len(raw_nodes) == 0:
            raise WorkflowValidationError("Workflow must contain a non-empty list of nodes.")

        graph = WorkflowGraph(raw_nodes, raw_edges)
        execution_order = graph.get_topological_order()

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

        if candidate_mode:
            context.variables["_candidate_mode"] = True
        else:
            self.active_contexts[exec_id] = context

        # Preserve prior metrics when resuming a paused execution
        prior_executed = sum(
            1 for s in context.node_states.values() if s == ExecutionStatus.SUCCESS
        )
        prior_skipped = sum(
            1 for s in context.node_states.values() if s == ExecutionStatus.SKIPPED
        )
        prior_failed = sum(
            1 for s in context.node_states.values() if s == ExecutionStatus.FAILED
        )
        perf_monitor = ExecutionPerformanceMonitor(
            execution_id=exec_id,
            workflow_id=workflow_id,
            prior_duration_ms=context.total_duration_ms,
            prior_node_durations=context.node_durations,
            prior_api_calls=context.total_api_calls,
            prior_token_usage=context.total_token_usage,
            prior_nodes_executed=prior_executed,
            prior_nodes_skipped=prior_skipped,
            prior_nodes_failed=prior_failed,
            prior_failed_node_id=context.failed_node_id,
        )

        final_output: Optional[Dict[str, Any]] = None
        skipped_nodes: Set[str] = set(context.skipped_nodes)
        untaken_edges_registry: Set[Tuple[str, str, Optional[str]]] = {
            tuple(item) for item in context.variables.get("_untaken_edges", [])
        }
        timeout_seconds = workflow.get("configuration", {}).get("timeoutSeconds")

        try:
            async def _run_nodes() -> Optional[ExecutionReportResponse]:
                nonlocal final_output
                for node_id in execution_order:
                    if node_id in context.completed_nodes:
                        node_obj = graph.nodes[node_id]
                        if node_obj.get("type") in ("Output", "output"):
                            final_output = context.node_outputs.get(node_id)
                        continue

                    node = graph.nodes[node_id]
                    node_name = node.get("name", node_id)
                    node_type = node.get("type", "Unknown")

                    if node_id in skipped_nodes:
                        context.skipped_nodes.add(node_id)
                        context.node_states[node_id] = ExecutionStatus.SKIPPED
                        perf_monitor.end_node(node_id, ExecutionStatus.SKIPPED)
                        context.node_durations[node_id] = 0.0

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

                    incoming_data = graph.get_incoming_data(
                        node_id, context.node_outputs, skipped_nodes=skipped_nodes
                    )

                    node_start_iso = utc_now_iso()
                    perf_monitor.start_node(node_id)
                    context.node_states[node_id] = ExecutionStatus.RUNNING

                    try:
                        handler = get_handler_for_node(node_type)
                        node_output = await handler.execute(node, incoming_data, context)

                        duration_ms = perf_monitor.end_node(
                            node_id,
                            ExecutionStatus.SUCCESS,
                            api_calls=handler.api_calls_made,
                            token_usage=handler.token_usage,
                        )

                        context.node_outputs[node_id] = node_output
                        context.node_states[node_id] = ExecutionStatus.SUCCESS
                        context.node_durations[node_id] = duration_ms
                        context.completed_nodes.add(node_id)
                        context.total_api_calls += handler.api_calls_made
                        if handler.token_usage:
                            context.total_token_usage.prompt_tokens += handler.token_usage.prompt_tokens
                            context.total_token_usage.completion_tokens += handler.token_usage.completion_tokens
                            context.total_token_usage.total_tokens += handler.token_usage.total_tokens

                        if node_type == "Condition" or str(node_type).lower() == "condition":
                            branch_taken = node_output.get("branch", "true")
                            new_skipped = graph.determine_skipped_nodes_for_condition(
                                node_id,
                                branch_taken,
                                existing_skipped=skipped_nodes,
                                untaken_edges_registry=untaken_edges_registry,
                            )
                            skipped_nodes.update(new_skipped)
                            context.skipped_nodes.update(new_skipped)
                            context.variables["_untaken_edges"] = [list(e) for e in untaken_edges_registry]

                        if node_type in ("Output", "output"):
                            final_output = node_output

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
                        duration_ms = perf_monitor.end_node(
                            node_id, ExecutionStatus.WAITING_FOR_APPROVAL
                        )
                        context.status = ExecutionStatus.WAITING_FOR_APPROVAL
                        context.waiting_node_id = node_id
                        context.node_states[node_id] = ExecutionStatus.WAITING_FOR_APPROVAL
                        context.node_durations[node_id] = duration_ms

                        waiting_log = NodeExecutionLog(
                            node_id=node_id,
                            node_name=node_name,
                            node_type=node_type,
                            status=ExecutionStatus.WAITING_FOR_APPROVAL,
                            start_time=node_start_iso,
                            end_time=utc_now_iso(),
                            duration_ms=duration_ms,
                            input_summary=self._safe_summary(incoming_data),
                            error_message=redact_text(har.message),
                        )
                        context.record_node_log(waiting_log)

                        metrics = perf_monitor.finish()
                        context.total_duration_ms = metrics.total_duration_ms
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
                        duration_ms = perf_monitor.end_node(node_id, ExecutionStatus.FAILED)
                        err_msg = redact_text(str(ne))
                        context.status = ExecutionStatus.FAILED
                        context.failed_node_id = node_id
                        context.errors[node_id] = err_msg
                        context.node_states[node_id] = ExecutionStatus.FAILED
                        context.node_durations[node_id] = duration_ms

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

                        curr_idx = execution_order.index(node_id)
                        for remaining_id in execution_order[curr_idx + 1 :]:
                            r_node = graph.nodes[remaining_id]
                            context.node_states[remaining_id] = ExecutionStatus.SKIPPED
                            perf_monitor.end_node(remaining_id, ExecutionStatus.SKIPPED)
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
                        context.total_duration_ms = metrics.total_duration_ms
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
                return None

            if timeout_seconds and isinstance(timeout_seconds, (int, float)) and timeout_seconds > 0:
                early_report = await asyncio.wait_for(_run_nodes(), timeout=float(timeout_seconds))
            else:
                early_report = await _run_nodes()

            if early_report is not None:
                return early_report

            context.status = ExecutionStatus.SUCCESS
            context.end_time = utc_now_iso()

            metrics = perf_monitor.finish()
            context.total_duration_ms = metrics.total_duration_ms

            if reexecution and original_duration_ms is not None:
                overhead = max(0.0, metrics.total_duration_ms - float(original_duration_ms))
                perf_monitor.record_reexecution_overhead(overhead)
                metrics = perf_monitor.finish()

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

        except asyncio.TimeoutError:
            context.status = ExecutionStatus.FAILED
            context.end_time = utc_now_iso()
            metrics = perf_monitor.finish()
            context.total_duration_ms = metrics.total_duration_ms
            return ExecutionReportResponse(
                execution_id=exec_id,
                workflow_id=workflow_id,
                workflow_version=workflow_version,
                status=ExecutionStatus.FAILED,
                start_time=context.start_time,
                end_time=context.end_time,
                total_duration_ms=metrics.total_duration_ms,
                error_message=f"Workflow execution timed out after {timeout_seconds}s.",
                node_logs=context.logs,
                metrics=metrics,
            )
        except Exception as e:
            if isinstance(e, ExecutionEngineError):
                raise
            raise ExecutionEngineError(f"Unexpected execution engine failure: {redact_text(str(e))}")

    async def resume_after_approval(
        self,
        workflow: Dict[str, Any],
        context: ExecutionContext,
        action: str,
        comment: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> ExecutionReportResponse:
        """Resumes a paused workflow execution following a human approval or rejection."""
        waiting_node_id = context.waiting_node_id
        if not waiting_node_id:
            raise WorkflowValidationError("No waiting human approval step found in context.")

        if action.lower() == "reject":
            reject_reason = (
                f"Execution rejected: {comment}"
                if comment
                else "Execution rejected by human approver."
            )
            context.variables.setdefault("_rejected_nodes", {})[waiting_node_id] = {
                "comment": reject_reason,
                "data": data,
            }
            context.status = ExecutionStatus.REJECTED
            context.waiting_node_id = None
            context.node_states[waiting_node_id] = ExecutionStatus.REJECTED
            context.end_time = utc_now_iso()

            for log in context.logs:
                if log.node_id == waiting_node_id:
                    log.status = ExecutionStatus.REJECTED
                    log.error_message = reject_reason

            prior_executed = sum(
                1 for s in context.node_states.values() if s == ExecutionStatus.SUCCESS
            )
            prior_skipped = sum(
                1 for s in context.node_states.values() if s == ExecutionStatus.SKIPPED
            )
            metrics = ExecutionPerformanceMonitor(
                execution_id=context.execution_id,
                workflow_id=context.workflow_id,
                prior_duration_ms=context.total_duration_ms,
                prior_node_durations=context.node_durations,
                prior_api_calls=context.total_api_calls,
                prior_token_usage=context.total_token_usage,
                prior_nodes_executed=prior_executed,
                prior_nodes_skipped=prior_skipped,
                prior_nodes_failed=1,
                prior_failed_node_id=waiting_node_id,
            ).finish()

            return ExecutionReportResponse(
                execution_id=context.execution_id,
                workflow_id=context.workflow_id,
                workflow_version=context.workflow_version,
                status=ExecutionStatus.REJECTED,
                start_time=context.start_time,
                end_time=context.end_time,
                total_duration_ms=metrics.total_duration_ms,
                error_message=reject_reason,
                failed_node_id=waiting_node_id,
                node_logs=context.logs,
                metrics=metrics,
            )

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
            return {"value": redact_text(str(data)[:300])}

        cleaned = redact_sensitive_data(data)
        sanitized: Dict[str, Any] = {}
        for k, v in cleaned.items():
            if isinstance(v, (str, bytes)):
                s = str(v)
                sanitized[k] = s[:300] + ("..." if len(s) > 300 else "")
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
