import time
from typing import Dict, Optional
from app.schemas.execution import ExecutionMetrics, TokenUsage, ExecutionStatus
from app.engine.pricing import calculate_estimated_cost_usd


class ExecutionPerformanceMonitor:
    """Tracks precision execution timings, API calls, token counts, and re-execution overhead."""

    def __init__(
        self,
        execution_id: str,
        workflow_id: Optional[str] = None,
        prior_duration_ms: float = 0.0,
        prior_node_durations: Optional[Dict[str, float]] = None,
        prior_api_calls: int = 0,
        prior_token_usage: Optional[TokenUsage] = None,
        prior_nodes_executed: int = 0,
        prior_nodes_skipped: int = 0,
        prior_nodes_failed: int = 0,
        prior_failed_node_id: Optional[str] = None,
    ):
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self._start_perf: float = time.perf_counter()
        self._prior_duration_ms: float = prior_duration_ms
        self._node_start_times: Dict[str, float] = {}
        self.node_durations_ms: Dict[str, float] = dict(prior_node_durations or {})
        self.total_api_calls: int = prior_api_calls
        self.prompt_tokens: int = prior_token_usage.prompt_tokens if prior_token_usage else 0
        self.completion_tokens: int = prior_token_usage.completion_tokens if prior_token_usage else 0
        self.total_tokens: int = prior_token_usage.total_tokens if prior_token_usage else 0
        self.has_tokens: bool = bool(prior_token_usage and prior_token_usage.total_tokens > 0)
        self.nodes_executed: int = prior_nodes_executed
        self.nodes_skipped: int = prior_nodes_skipped
        self.nodes_failed: int = prior_nodes_failed
        self.failed_node_id: Optional[str] = prior_failed_node_id
        self.reexecution_overhead_ms: Optional[float] = None
        self.model_used: Optional[str] = None

    def start_node(self, node_id: str) -> None:
        self._node_start_times[node_id] = time.perf_counter()

    def end_node(
        self,
        node_id: str,
        status: ExecutionStatus,
        api_calls: int = 0,
        token_usage: Optional[TokenUsage] = None,
        model_name: Optional[str] = None,
    ) -> float:
        start = self._node_start_times.get(node_id, time.perf_counter())
        duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
        self.node_durations_ms[node_id] = duration_ms

        if status == ExecutionStatus.SUCCESS:
            self.nodes_executed += 1
        elif status == ExecutionStatus.FAILED:
            self.nodes_failed += 1
            self.failed_node_id = node_id
        elif status == ExecutionStatus.SKIPPED:
            self.nodes_skipped += 1

        self.total_api_calls += api_calls
        if model_name:
            self.model_used = model_name
        if token_usage:
            self.has_tokens = True
            self.prompt_tokens += token_usage.prompt_tokens
            self.completion_tokens += token_usage.completion_tokens
            self.total_tokens += token_usage.total_tokens

        return duration_ms

    def record_reexecution_overhead(self, overhead_ms: float) -> None:
        self.reexecution_overhead_ms = round(max(0.0, overhead_ms), 2)

    def finish(self, default_model: Optional[str] = None) -> ExecutionMetrics:
        elapsed_ms = (time.perf_counter() - self._start_perf) * 1000.0
        total_duration = round(self._prior_duration_ms + elapsed_ms, 2)
        total_tokens_obj = None
        estimated_cost: Optional[float] = None
        if self.has_tokens:
            total_tokens_obj = TokenUsage(
                prompt_tokens=self.prompt_tokens,
                completion_tokens=self.completion_tokens,
                total_tokens=self.total_tokens,
            )
            estimated_cost = calculate_estimated_cost_usd(
                self.model_used or default_model,
                self.prompt_tokens,
                self.completion_tokens,
            )

        return ExecutionMetrics(
            execution_id=self.execution_id,
            workflow_id=self.workflow_id,
            total_duration_ms=total_duration,
            node_durations_ms=self.node_durations_ms,
            total_api_calls=self.total_api_calls,
            total_token_usage=total_tokens_obj,
            estimated_cost_usd=estimated_cost,
            nodes_executed=self.nodes_executed,
            nodes_skipped=self.nodes_skipped,
            nodes_failed=self.nodes_failed,
            failed_node_id=self.failed_node_id,
            reexecution_overhead_ms=self.reexecution_overhead_ms,
        )
