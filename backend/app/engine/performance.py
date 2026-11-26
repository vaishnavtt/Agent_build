import time
from typing import Dict, Any, Optional
from app.schemas.execution import ExecutionMetrics, TokenUsage, ExecutionStatus


class ExecutionPerformanceMonitor:
    """Tracks precision execution timings, API calls, token counts, and re-execution overhead."""

    def __init__(self, execution_id: str, workflow_id: Optional[str] = None):
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self._start_perf: float = time.perf_counter()
        self._node_start_times: Dict[str, float] = {}
        self.node_durations_ms: Dict[str, float] = {}
        self.total_api_calls: int = 0
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.total_tokens: int = 0
        self.has_tokens: bool = False
        self.nodes_executed: int = 0
        self.nodes_skipped: int = 0
        self.nodes_failed: int = 0
        self.failed_node_id: Optional[str] = None
        self.reexecution_overhead_ms: Optional[float] = None

    def start_node(self, node_id: str) -> None:
        self._node_start_times[node_id] = time.perf_counter()

    def end_node(
        self,
        node_id: str,
        status: ExecutionStatus,
        api_calls: int = 0,
        token_usage: Optional[TokenUsage] = None,
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
        if token_usage:
            self.has_tokens = True
            self.prompt_tokens += token_usage.prompt_tokens
            self.completion_tokens += token_usage.completion_tokens
            self.total_tokens += token_usage.total_tokens

        return duration_ms

    def record_reexecution_overhead(self, overhead_ms: float) -> None:
        self.reexecution_overhead_ms = round(overhead_ms, 2)

    def finish(self) -> ExecutionMetrics:
        total_duration = round((time.perf_counter() - self._start_perf) * 1000.0, 2)
        total_tokens_obj = None
        if self.has_tokens:
            total_tokens_obj = TokenUsage(
                prompt_tokens=self.prompt_tokens,
                completion_tokens=self.completion_tokens,
                total_tokens=self.total_tokens,
            )

        return ExecutionMetrics(
            execution_id=self.execution_id,
            workflow_id=self.workflow_id,
            total_duration_ms=total_duration,
            node_durations_ms=self.node_durations_ms,
            total_api_calls=self.total_api_calls,
            total_token_usage=total_tokens_obj,
            nodes_executed=self.nodes_executed,
            nodes_skipped=self.nodes_skipped,
            nodes_failed=self.nodes_failed,
            failed_node_id=self.failed_node_id,
            reexecution_overhead_ms=self.reexecution_overhead_ms,
        )
