import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.reliability import ScenarioResult
from app.services.reliability import ReliabilityLabService, ReliabilityScorer

client = TestClient(app)


def _create_workflow(input_type="text", required=True, description="Analyze support request.", valid=True):
    nodes = [
        {
            "id": "input-1",
            "type": "customWorkflow",
            "data": {
                "label": "Workflow Input",
                "componentType": "Input",
                "config": {"inputType": input_type, "required": required},
            },
        },
        {
            "id": "llm-1",
            "type": "customWorkflow",
            "data": {
                "label": "Gemini Model",
                "componentType": "LLM",
                "config": {
                    "model": "gemini-1.5-pro",
                    "systemPrompt": "Analyze carefully." if valid else "",
                },
            },
        },
        {
            "id": "output-1",
            "type": "customWorkflow",
            "data": {
                "label": "Workflow Output",
                "componentType": "Output",
                "config": {"outputFormat": "markdown"},
            },
        },
    ]
    edges = [
        {
            "id": "e1",
            "source": "input-1",
            "target": "llm-1",
            "sourceHandle": "output",
            "targetHandle": "prompt",
        },
        {
            "id": "e2",
            "source": "llm-1",
            "target": "output-1",
            "sourceHandle": "response",
            "targetHandle": "input",
        },
    ]
    res = client.post(
        "/api/v1/workflows",
        json={
            "name": f"Reliability Test ({input_type})",
            "description": description,
            "version": "1.0.0",
            "nodes": nodes,
            "edges": edges,
        },
    )
    assert res.status_code == 201
    return res.json()["id"]


def test_reliability_scenarios_endpoint_all_categories_and_not_run():
    wf_id = _create_workflow(input_type="text", required=True)
    try:
        res = client.post(f"/api/v1/workflows/{wf_id}/reliability/scenarios")
        assert res.status_code == 200
        body = res.json()

        assert body["workflow_id"] == wf_id
        assert body["input_type_detected"] == "text"
        assert body["validation_passed"] is True

        grouped = body["scenarios_by_category"]
        assert set(grouped.keys()) == {"normal", "robustness", "edge"}
        assert len(grouped["normal"]) >= 1
        assert len(grouped["robustness"]) >= 2
        assert len(grouped["edge"]) >= 2

        total = sum(len(grouped[k]) for k in grouped)
        assert body["total_scenarios"] == total

        for cat, items in grouped.items():
            for item in items:
                assert item["category"] == cat
                assert item["status"] == "NOT_RUN"
                assert item["stress_vector"]
                if cat == "normal":
                    assert item["expected_handling"] == "SUCCESS"
                elif cat == "robustness":
                    assert item["expected_handling"] == "SAFE_REJECTION"
                elif cat == "edge":
                    assert item["expected_handling"] == "GRACEFUL_HANDLING"
    finally:
        client.delete(f"/api/v1/workflows/{wf_id}")


def test_reliability_scenarios_deterministic_ids_and_input_types():
    for itype in ("text", "json", "file_url"):
        wf_id = _create_workflow(input_type=itype, required=True)
        try:
            r1 = client.post(f"/api/v1/workflows/{wf_id}/reliability/scenarios").json()
            r2 = client.post(f"/api/v1/workflows/{wf_id}/reliability/scenarios").json()
            ids1 = [s["scenario_id"] for cat in r1["scenarios_by_category"].values() for s in cat]
            ids2 = [s["scenario_id"] for cat in r2["scenarios_by_category"].values() for s in cat]
            assert ids1 == ids2
            assert len(ids1) == len(set(ids1))
        finally:
            client.delete(f"/api/v1/workflows/{wf_id}")


def test_reliability_scenarios_invalid_and_nonexistent_workflow():
    bad_wf_id = _create_workflow(valid=False)
    try:
        res = client.post(f"/api/v1/workflows/{bad_wf_id}/reliability/scenarios")
        assert res.status_code == 400
        assert "validation_errors" in res.json()["detail"]
    finally:
        client.delete(f"/api/v1/workflows/{bad_wf_id}")

    missing_res = client.post("/api/v1/workflows/missing-wf-000/reliability/scenarios")
    assert missing_res.status_code == 404


def test_scorer_no_executed_scenarios_returns_none():
    scorer = ReliabilityScorer()
    results = [
        ScenarioResult(
            scenario_id="rel-norm-1",
            category="normal",
            stress_vector="BASELINE_VALID_INPUT",
            expected_handling="SUCCESS",
            status="NOT_RUN",
        ),
        ScenarioResult(
            scenario_id="rel-rob-1",
            category="robustness",
            stress_vector="EMPTY_INPUT",
            expected_handling="SAFE_REJECTION",
            status="NOT_RUN",
        ),
    ]
    breakdown = scorer.score(results)
    assert breakdown.final_score is None
    assert breakdown.normal.completed == 0
    assert breakdown.normal.earned_points is None
    assert breakdown.robustness.completed == 0


def test_scorer_proportional_calculation_and_empty_categories():
    scorer = ReliabilityScorer()
    # 2/2 normal passed (40 pts), 1/2 robustness passed (15 pts), 0 edge scenarios (empty category)
    results = [
        ScenarioResult(
            scenario_id="n1", category="normal", stress_vector="V", expected_handling="SUCCESS", status="PASSED"
        ),
        ScenarioResult(
            scenario_id="n2", category="normal", stress_vector="V", expected_handling="SUCCESS", status="PASSED"
        ),
        ScenarioResult(
            scenario_id="r1", category="robustness", stress_vector="V", expected_handling="SAFE_REJECTION", status="PASSED"
        ),
        ScenarioResult(
            scenario_id="r2", category="robustness", stress_vector="V", expected_handling="SAFE_REJECTION", status="FAILED"
        ),
    ]
    breakdown = scorer.score(results)
    assert breakdown.normal.earned_points == 40.0
    assert breakdown.robustness.earned_points == 15.0
    assert breakdown.edge.completed == 0
    assert breakdown.edge.earned_points is None
    assert breakdown.final_score == 55.0


def test_scorer_critical_deductions():
    scorer = ReliabilityScorer()
    # 1/1 normal (40), 0/1 robustness with UNHANDLED_CRASH (-15), 0/1 edge with TIMEOUT_VIOLATION (-10),
    # plus 0/1 edge with CORRUPTED_OUTPUT (-20) -> 40 - 45 = 0 (clamped at 0)
    results = [
        ScenarioResult(
            scenario_id="n1", category="normal", stress_vector="V", expected_handling="SUCCESS", status="PASSED"
        ),
        ScenarioResult(
            scenario_id="r1",
            category="robustness",
            stress_vector="V",
            expected_handling="SAFE_REJECTION",
            status="FAILED",
            critical_defect="UNHANDLED_CRASH",
        ),
        ScenarioResult(
            scenario_id="e1",
            category="edge",
            stress_vector="V",
            expected_handling="GRACEFUL_HANDLING",
            status="FAILED",
            critical_defect="TIMEOUT_VIOLATION",
        ),
        ScenarioResult(
            scenario_id="e2",
            category="edge",
            stress_vector="V",
            expected_handling="GRACEFUL_HANDLING",
            status="FAILED",
            critical_defect="CORRUPTED_OUTPUT",
        ),
    ]
    breakdown = scorer.score(results)
    assert breakdown.unhandled_crashes == 1
    assert breakdown.timeout_violations == 1
    assert breakdown.corrupted_outputs == 1
    assert breakdown.total_deductions == 45.0
    assert breakdown.final_score == 0.0


def test_report_generation_and_failure_diagnostic_payload():
    lab = ReliabilityLabService()
    grouped, _, _ = lab.generate_scenarios(
        nodes=[
            {
                "id": "input-1",
                "type": "Input",
                "config": {"inputType": "text", "required": True},
            },
            {
                "id": "llm-1",
                "type": "LLM",
                "config": {"model": "gemini-1.5-pro", "systemPrompt": "Be helpful."},
            },
            {
                "id": "output-1",
                "type": "Output",
                "config": {"outputFormat": "markdown"},
            },
        ],
        edges=[
            {"id": "e1", "source": "input-1", "target": "llm-1"},
            {"id": "e2", "source": "llm-1", "target": "output-1"},
        ],
        requirement="Answer user questions.",
        workflow_name="QA Agent",
    )
    all_scenarios = [s for cat in grouped.values() for s in cat]

    # Report with no executed results -> reliability_score must be None
    empty_report = lab.build_report("wf-1", "QA Agent", all_scenarios, supplied_results=None)
    assert empty_report.executed_scenarios == 0
    assert empty_report.not_run_scenarios == len(all_scenarios)
    assert empty_report.reliability_score is None
    assert empty_report.failure_diagnostics == []

    # Report with unit-test simulated results (1 passed normal, 1 failed robustness crash)
    norm_s = grouped["normal"][0]
    rob_s = grouped["robustness"][0]
    supplied = [
        ScenarioResult(
            scenario_id=norm_s.scenario_id,
            category="normal",
            stress_vector=norm_s.stress_vector,
            expected_handling="SUCCESS",
            actual_handling="SUCCESS",
            status="PASSED",
            duration_ms=120.0,
        ),
        ScenarioResult(
            scenario_id=rob_s.scenario_id,
            category="robustness",
            stress_vector=rob_s.stress_vector,
            expected_handling="SAFE_REJECTION",
            actual_handling="CRASH_500",
            status="FAILED",
            critical_defect="UNHANDLED_CRASH",
            error_message="Unhandled ValueError in input-1",
            stack_trace="Traceback...",
            failing_node_id="input-1",
            failing_node_type="Input",
            duration_ms=15.0,
        ),
    ]
    report = lab.build_report("wf-1", "QA Agent", all_scenarios, supplied_results=supplied)
    assert report.executed_scenarios == 2
    assert report.passed_scenarios == 1
    assert report.failed_scenarios == 1
    # 40 (normal) + 0 (robustness) - 15 (crash) = 25.0
    assert report.reliability_score == 25.0
    assert len(report.failure_diagnostics) == 1

    diag = report.failure_diagnostics[0]
    assert diag.workflow_id == "wf-1"
    assert diag.scenario_id == rob_s.scenario_id
    assert diag.failure_type == "UNCAUGHT_EXCEPTION"
    assert diag.failing_node_id == "input-1"
    assert diag.input_payload == rob_s.sample_input
    assert diag.error_message == "Unhandled ValueError in input-1"
