import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas.regression import (
    BaselineSnapshot,
    RegressionDiff,
    RegressionReport,
    RegressionVerdict,
)
from app.schemas.reliability import FailureDiagnosticPayload, ScenarioResult
from app.services.regression.result_comparator import (
    RegressionComparisonError,
    ResultComparator,
)
from app.services.reliability.reliability_lab import _map_failure_type
from app.services.reliability.reliability_scorer import ReliabilityScorer


def compute_workflow_fingerprint(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
    """Compute a deterministic SHA-256 fingerprint for a workflow's topology and configs."""
    canonical = json.dumps({"nodes": nodes, "edges": edges}, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


class RegressionService:
    """Compares pre-repair baseline snapshots against post-repair results and builds RegressionReports."""

    def __init__(self) -> None:
        self._comparator = ResultComparator()
        self._scorer = ReliabilityScorer()

    def compare_and_report(
        self,
        workflow_id: str,
        baseline: BaselineSnapshot,
        post_repair_results: List[ScenarioResult],
        post_repair_version: Optional[str] = None,
        post_repair_fingerprint: Optional[str] = None,
    ) -> RegressionReport:
        if baseline.workflow_id != workflow_id:
            raise RegressionComparisonError(
                f"Workflow ID mismatch: endpoint workflow_id '{workflow_id}' does not match "
                f"baseline.workflow_id '{baseline.workflow_id}'."
            )

        diff = self._comparator.compare(baseline=baseline, post_repair_results=post_repair_results)

        # Compute pre-repair and post-repair scores using Stage 3 ReliabilityScorer
        baseline_as_results = [
            ScenarioResult(
                scenario_id=e.scenario_id,
                category=e.category,
                stress_vector=e.stress_vector,
                expected_handling=e.expected_handling,
                actual_handling=e.actual_handling,
                status=e.status,
                critical_defect=e.critical_defect,
                actual_output=e.actual_output,
                error_message=e.error_message,
                stack_trace=e.stack_trace,
                failing_node_id=e.failing_node_id,
                failing_node_type=e.failing_node_type,
                duration_ms=e.duration_ms,
            )
            for e in baseline.baseline_results
        ]

        pre_score = self._scorer.score(baseline_as_results).final_score
        post_score = self._scorer.score(post_repair_results).final_score
        delta_score: Optional[float] = (
            round(post_score - pre_score, 2)
            if (pre_score is not None and post_score is not None)
            else None
        )

        verdict = self._determine_verdict(diff)

        now = datetime.now(timezone.utc)
        post_by_id = {r.scenario_id: r for r in post_repair_results}
        baseline_by_id = {e.scenario_id: e for e in baseline.baseline_results}

        failure_diagnostics: List[FailureDiagnosticPayload] = []
        for transition in diff.transitions:
            if transition.classification in ("REGRESSION", "UNRESOLVED"):
                post_res = post_by_id.get(transition.scenario_id)
                base_entry = baseline_by_id[transition.scenario_id]
                if post_res is not None:
                    failure_diagnostics.append(
                        FailureDiagnosticPayload(
                            workflow_id=workflow_id,
                            scenario_id=transition.scenario_id,
                            category=transition.category,
                            stress_vector=post_res.stress_vector,
                            failure_type=_map_failure_type(post_res),
                            failing_node_id=post_res.failing_node_id,
                            failing_node_type=post_res.failing_node_type,
                            input_payload=base_entry.sample_input,
                            expected_handling=base_entry.expected_handling,
                            actual_handling=post_res.actual_handling,
                            actual_output=post_res.actual_output,
                            error_message=post_res.error_message,
                            stack_trace=post_res.stack_trace,
                            timestamp=now,
                        )
                    )

        summary = (
            f"Regression verdict: {verdict}. "
            f"Fixed={diff.fixed_count}, Unresolved={diff.unresolved_count}, "
            f"Stable={diff.stable_count}, Regressions={diff.regression_count}, "
            f"Incomplete={diff.incomplete_count}."
        )

        return RegressionReport(
            workflow_id=workflow_id,
            pre_repair_version=baseline.workflow_version,
            pre_repair_fingerprint=baseline.workflow_fingerprint,
            post_repair_version=post_repair_version,
            post_repair_fingerprint=post_repair_fingerprint,
            generated_at=now,
            total_scenarios=diff.total_scenarios,
            fixed_count=diff.fixed_count,
            unresolved_count=diff.unresolved_count,
            stable_count=diff.stable_count,
            regression_count=diff.regression_count,
            incomplete_count=diff.incomplete_count,
            pre_repair_score=pre_score,
            post_repair_score=post_score,
            delta_score=delta_score,
            verdict=verdict,
            diff=diff,
            failure_diagnostics=failure_diagnostics,
            summary=summary,
        )

    def _determine_verdict(self, diff: RegressionDiff) -> RegressionVerdict:
        if diff.regression_count > 0:
            return "REGRESSION_DETECTED"
        if diff.incomplete_count > 0:
            return "INCOMPLETE"
        if diff.unresolved_count == 0:
            return "VERIFIED_SUCCESS"
        if diff.fixed_count > 0:
            return "PARTIAL_SUCCESS"
        return "UNRESOLVED"
