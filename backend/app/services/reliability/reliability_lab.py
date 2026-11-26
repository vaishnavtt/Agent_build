from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.reliability import (
    FailureDiagnosticPayload,
    FailureType,
    ReliabilityCategory,
    ReliabilityReport,
    ReliabilityScenario,
    ScenarioResult,
)
from app.services.reliability.reliability_scorer import ReliabilityScorer
from app.services.reliability.scenario_generator import ReliabilityScenarioGenerator


def _map_failure_type(res: ScenarioResult) -> FailureType:
    if res.critical_defect == "UNHANDLED_CRASH":
        return "UNCAUGHT_EXCEPTION"
    if res.critical_defect == "TIMEOUT_VIOLATION":
        return "TIMEOUT"
    if res.critical_defect == "CORRUPTED_OUTPUT":
        return "CORRUPTED_OUTPUT"
    if res.category == "robustness":
        return "ROBUSTNESS_BREACH"
    return "EXECUTION_FAILURE"


class ReliabilityLabService:
    """Coordinates reliability scenario generation, deterministic scoring, and report synthesis."""

    def __init__(self) -> None:
        self._scenario_generator = ReliabilityScenarioGenerator()
        self._scorer = ReliabilityScorer()

    def generate_scenarios(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        requirement: Optional[str] = None,
        workflow_name: str = "Workflow",
    ) -> Tuple[Dict[ReliabilityCategory, List[ReliabilityScenario]], str, bool]:
        return self._scenario_generator.generate(
            nodes=nodes,
            edges=edges,
            requirement=requirement,
            workflow_name=workflow_name,
        )

    def build_report(
        self,
        workflow_id: str,
        workflow_name: str,
        scenarios: List[ReliabilityScenario],
        supplied_results: Optional[List[ScenarioResult]] = None,
    ) -> ReliabilityReport:
        """Assemble a ReliabilityReport from scenarios and any genuine supplied ScenarioResults."""
        result_by_id: Dict[str, ScenarioResult] = {
            r.scenario_id: r for r in (supplied_results or [])
        }
        scenario_by_id: Dict[str, ReliabilityScenario] = {
            s.scenario_id: s for s in scenarios
        }

        aligned_results: List[ScenarioResult] = []
        for scenario in scenarios:
            if scenario.scenario_id in result_by_id:
                res = result_by_id[scenario.scenario_id]
                if res.status == "PASSED":
                    res = res.model_copy(update={"passed": True})
                elif res.status == "FAILED":
                    res = res.model_copy(update={"passed": False})
                else:
                    res = res.model_copy(update={"passed": None})
                aligned_results.append(res)
            else:
                aligned_results.append(
                    ScenarioResult(
                        scenario_id=scenario.scenario_id,
                        category=scenario.category,
                        stress_vector=scenario.stress_vector,
                        expected_handling=scenario.expected_handling,
                        status="NOT_RUN",
                        passed=None,
                    )
                )

        score_breakdown = self._scorer.score(aligned_results)

        executed = sum(1 for r in aligned_results if r.status != "NOT_RUN")
        not_run = sum(1 for r in aligned_results if r.status == "NOT_RUN")
        passed = sum(1 for r in aligned_results if r.status == "PASSED")
        failed = sum(1 for r in aligned_results if r.status == "FAILED")

        now = datetime.now(timezone.utc)
        failure_diagnostics: List[FailureDiagnosticPayload] = []
        for res in aligned_results:
            if res.status == "FAILED":
                scen = scenario_by_id.get(res.scenario_id)
                failure_diagnostics.append(
                    FailureDiagnosticPayload(
                        workflow_id=workflow_id,
                        scenario_id=res.scenario_id,
                        category=res.category,
                        stress_vector=res.stress_vector,
                        failure_type=_map_failure_type(res),
                        failing_node_id=res.failing_node_id,
                        failing_node_type=res.failing_node_type,
                        input_payload=scen.sample_input if scen else {},
                        expected_handling=res.expected_handling,
                        actual_handling=res.actual_handling,
                        actual_output=res.actual_output,
                        error_message=res.error_message,
                        stack_trace=res.stack_trace,
                        timestamp=now,
                    )
                )

        if executed == 0:
            summary = (
                f"Generated {len(aligned_results)} reliability scenarios; "
                "0 executed (status: NOT_RUN). Reliability score cannot be calculated until execution."
            )
        else:
            summary = (
                f"Executed {executed}/{len(aligned_results)} scenarios: "
                f"{passed} passed, {failed} failed. "
                f"Reliability score: {score_breakdown.final_score}."
            )

        return ReliabilityReport(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            generated_at=now,
            total_scenarios=len(aligned_results),
            executed_scenarios=executed,
            not_run_scenarios=not_run,
            passed_scenarios=passed,
            failed_scenarios=failed,
            reliability_score=score_breakdown.final_score,
            score_breakdown=score_breakdown,
            scenario_results=aligned_results,
            failure_diagnostics=failure_diagnostics,
            summary=summary,
        )
