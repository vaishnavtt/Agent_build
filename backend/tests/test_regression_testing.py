from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.regression import BaselineScenarioEntry, BaselineSnapshot
from app.schemas.reliability import ScenarioResult
from app.services.regression import (
    RegressionComparisonError,
    RegressionService,
    ResultComparator,
)

client = TestClient(app)


def _baseline_entry(
    scenario_id: str,
    status: str,
    category: str = "normal",
    expected_handling: str = "SUCCESS",
    error_message: str | None = None,
) -> BaselineScenarioEntry:
    return BaselineScenarioEntry(
        scenario_id=scenario_id,
        category=category,
        stress_vector="BASELINE_VALID_INPUT" if category == "normal" else "EMPTY_INPUT",
        sample_input={"input": f"sample-{scenario_id}"},
        expected_handling=expected_handling,
        status=status,
        error_message=error_message,
    )


def _post_result(
    scenario_id: str,
    status: str,
    category: str = "normal",
    expected_handling: str = "SUCCESS",
    error_message: str | None = None,
    critical_defect: str | None = None,
) -> ScenarioResult:
    return ScenarioResult(
        scenario_id=scenario_id,
        category=category,
        stress_vector="BASELINE_VALID_INPUT" if category == "normal" else "EMPTY_INPUT",
        expected_handling=expected_handling,
        status=status,
        error_message=error_message,
        critical_defect=critical_defect,
    )


def _create_persisted_workflow() -> str:
    res = client.post(
        "/api/v1/workflows",
        json={
            "name": "Regression Test Workflow",
            "description": "Workflow for regression API tests",
            "version": "1.0.0",
            "nodes": [
                {"id": "n1", "type": "Input", "config": {"inputType": "text"}},
                {"id": "n2", "type": "Output", "config": {"outputFormat": "markdown"}},
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        },
    )
    assert res.status_code == 201
    return res.json()["id"]


def test_fixed_and_stable_verified_success():
    svc = RegressionService()
    baseline = BaselineSnapshot(
        workflow_id="wf-1",
        workflow_version="1.0.0",
        tested_at=datetime.now(timezone.utc),
        baseline_results=[
            _baseline_entry("s1", "FAILED", "normal", "SUCCESS", "Initial failure"),
            _baseline_entry("s2", "PASSED", "robustness", "SAFE_REJECTION"),
        ],
    )
    post = [
        _post_result("s1", "PASSED", "normal", "SUCCESS"),
        _post_result("s2", "PASSED", "robustness", "SAFE_REJECTION"),
    ]
    report = svc.compare_and_report("wf-1", baseline, post, post_repair_version="1.0.1")

    assert report.verdict == "VERIFIED_SUCCESS"
    assert report.fixed_count == 1
    assert report.stable_count == 1
    assert report.unresolved_count == 0
    assert report.regression_count == 0
    assert report.incomplete_count == 0
    assert report.pre_repair_score == 30.0  # 0/1 normal (0) + 1/1 robustness (30)
    assert report.post_repair_score == 70.0  # 1/1 normal (40) + 1/1 robustness (30)
    assert report.delta_score == 40.0
    assert report.failure_diagnostics == []
    assert report.diff.transitions[0].sample_input == {"input": "sample-s1"}


def test_unresolved_verdict():
    svc = RegressionService()
    baseline = BaselineSnapshot(
        workflow_id="wf-1",
        tested_at=datetime.now(timezone.utc),
        baseline_results=[_baseline_entry("s1", "FAILED", "normal", "SUCCESS", "Still broken")],
    )
    post = [_post_result("s1", "FAILED", "normal", "SUCCESS", "Still broken", "UNHANDLED_CRASH")]
    report = svc.compare_and_report("wf-1", baseline, post)

    assert report.verdict == "UNRESOLVED"
    assert report.unresolved_count == 1
    assert report.fixed_count == 0
    assert len(report.failure_diagnostics) == 1
    assert report.failure_diagnostics[0].failure_type == "UNCAUGHT_EXCEPTION"


def test_partial_success_verdict():
    svc = RegressionService()
    baseline = BaselineSnapshot(
        workflow_id="wf-1",
        tested_at=datetime.now(timezone.utc),
        baseline_results=[
            _baseline_entry("s1", "FAILED", "normal", "SUCCESS", "Err 1"),
            _baseline_entry("s2", "FAILED", "robustness", "SAFE_REJECTION", "Err 2"),
        ],
    )
    post = [
        _post_result("s1", "PASSED", "normal", "SUCCESS"),
        _post_result("s2", "FAILED", "robustness", "SAFE_REJECTION", "Err 2"),
    ]
    report = svc.compare_and_report("wf-1", baseline, post)

    assert report.verdict == "PARTIAL_SUCCESS"
    assert report.fixed_count == 1
    assert report.unresolved_count == 1
    assert report.regression_count == 0


def test_regression_detected_with_mixed_outcomes():
    svc = RegressionService()
    baseline = BaselineSnapshot(
        workflow_id="wf-1",
        tested_at=datetime.now(timezone.utc),
        baseline_results=[
            _baseline_entry("s1", "FAILED", "normal", "SUCCESS", "Old bug"),
            _baseline_entry("s2", "PASSED", "robustness", "SAFE_REJECTION"),
            _baseline_entry("s3", "PASSED", "edge", "GRACEFUL_HANDLING"),
        ],
    )
    post = [
        _post_result("s1", "PASSED", "normal", "SUCCESS"),
        _post_result("s2", "PASSED", "robustness", "SAFE_REJECTION"),
        _post_result("s3", "FAILED", "edge", "GRACEFUL_HANDLING", "New regression!"),
    ]
    report = svc.compare_and_report("wf-1", baseline, post)

    assert report.verdict == "REGRESSION_DETECTED"
    assert report.fixed_count == 1
    assert report.stable_count == 1
    assert report.regression_count == 1
    assert len(report.failure_diagnostics) == 1
    assert report.failure_diagnostics[0].scenario_id == "s3"


def test_missing_post_repair_results_yields_incomplete():
    svc = RegressionService()
    baseline = BaselineSnapshot(
        workflow_id="wf-1",
        tested_at=datetime.now(timezone.utc),
        baseline_results=[
            _baseline_entry("s1", "FAILED", "normal", "SUCCESS"),
            _baseline_entry("s2", "PASSED", "robustness", "SAFE_REJECTION"),
        ],
    )
    post = [_post_result("s1", "PASSED", "normal", "SUCCESS")]
    report = svc.compare_and_report("wf-1", baseline, post)

    assert report.verdict == "INCOMPLETE"
    assert report.fixed_count == 1
    assert report.incomplete_count == 1
    assert report.diff.missing_post_repair_ids == ["s2"]


def test_not_run_scenarios_yields_incomplete_and_null_score():
    svc = RegressionService()
    baseline = BaselineSnapshot(
        workflow_id="wf-1",
        tested_at=datetime.now(timezone.utc),
        baseline_results=[_baseline_entry("s1", "NOT_RUN", "normal", "SUCCESS")],
    )
    post = [_post_result("s1", "NOT_RUN", "normal", "SUCCESS")]
    report = svc.compare_and_report("wf-1", baseline, post)

    assert report.verdict == "INCOMPLETE"
    assert report.incomplete_count == 1
    assert report.pre_repair_score is None
    assert report.post_repair_score is None
    assert report.delta_score is None


def test_comparator_rejects_duplicates_unexpected_ids_and_empty_baseline():
    comparator = ResultComparator()

    empty_base = BaselineSnapshot(
        workflow_id="wf-1", tested_at=datetime.now(timezone.utc), baseline_results=[]
    )
    with pytest.raises(RegressionComparisonError, match="no scenarios"):
        comparator.compare(empty_base, [])

    dup_base = BaselineSnapshot(
        workflow_id="wf-1",
        tested_at=datetime.now(timezone.utc),
        baseline_results=[
            _baseline_entry("s1", "FAILED"),
            _baseline_entry("s1", "PASSED"),
        ],
    )
    with pytest.raises(RegressionComparisonError, match="Duplicate scenario_id"):
        comparator.compare(dup_base, [_post_result("s1", "PASSED")])

    valid_base = BaselineSnapshot(
        workflow_id="wf-1",
        tested_at=datetime.now(timezone.utc),
        baseline_results=[_baseline_entry("s1", "FAILED")],
    )
    with pytest.raises(RegressionComparisonError, match="Duplicate scenario_id"):
        comparator.compare(valid_base, [_post_result("s1", "PASSED"), _post_result("s1", "PASSED")])

    with pytest.raises(RegressionComparisonError, match="Unexpected post-repair"):
        comparator.compare(valid_base, [_post_result("s1", "PASSED"), _post_result("s99", "PASSED")])


def test_workflow_id_mismatch_raises_error():
    svc = RegressionService()
    baseline = BaselineSnapshot(
        workflow_id="wf-other",
        tested_at=datetime.now(timezone.utc),
        baseline_results=[_baseline_entry("s1", "FAILED")],
    )
    with pytest.raises(RegressionComparisonError, match="Workflow ID mismatch"):
        svc.compare_and_report("wf-1", baseline, [_post_result("s1", "PASSED")])


def test_regression_compare_endpoint_and_404():
    wf_id = _create_persisted_workflow()
    try:
        payload = {
            "baseline": {
                "workflow_id": wf_id,
                "workflow_version": "1.0.0",
                "tested_at": datetime.now(timezone.utc).isoformat(),
                "baseline_results": [
                    {
                        "scenario_id": "rel-norm-1",
                        "category": "normal",
                        "stress_vector": "BASELINE_VALID_INPUT",
                        "sample_input": {"input": "hello"},
                        "expected_handling": "SUCCESS",
                        "status": "FAILED",
                        "error_message": "Missing prompt",
                    }
                ],
            },
            "post_repair_results": [
                {
                    "scenario_id": "rel-norm-1",
                    "category": "normal",
                    "stress_vector": "BASELINE_VALID_INPUT",
                    "expected_handling": "SUCCESS",
                    "status": "PASSED",
                }
            ],
        }
        res = client.post(f"/api/v1/workflows/{wf_id}/regression/compare", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["workflow_id"] == wf_id
        assert body["verdict"] == "VERIFIED_SUCCESS"
        assert body["fixed_count"] == 1
        assert body["delta_score"] == 40.0
        assert body["post_repair_fingerprint"] is not None
    finally:
        client.delete(f"/api/v1/workflows/{wf_id}")

    res_404 = client.post(
        "/api/v1/workflows/nonexistent-wf/regression/compare",
        json={
            "baseline": {
                "workflow_id": "nonexistent-wf",
                "tested_at": datetime.now(timezone.utc).isoformat(),
                "baseline_results": [
                    {
                        "scenario_id": "s1",
                        "category": "normal",
                        "sample_input": {"input": "x"},
                        "expected_handling": "SUCCESS",
                        "status": "FAILED",
                    }
                ],
            },
            "post_repair_results": [],
        },
    )
    assert res_404.status_code == 404


def test_regression_compare_endpoint_rejects_duplicate_baseline_scenario_ids():
    wf_id = _create_persisted_workflow()
    try:
        payload = {
            "baseline": {
                "workflow_id": wf_id,
                "workflow_version": "1.0.0",
                "tested_at": datetime.now(timezone.utc).isoformat(),
                "baseline_results": [
                    {
                        "scenario_id": "dup-1",
                        "category": "normal",
                        "stress_vector": "BASELINE_VALID_INPUT",
                        "sample_input": {"input": "hello"},
                        "expected_handling": "SUCCESS",
                        "status": "FAILED",
                        "error_message": "First failure",
                    },
                    {
                        "scenario_id": "dup-1",
                        "category": "normal",
                        "stress_vector": "BASELINE_VALID_INPUT",
                        "sample_input": {"input": "hello again"},
                        "expected_handling": "SUCCESS",
                        "status": "PASSED",
                    },
                ],
            },
            "post_repair_results": [
                {
                    "scenario_id": "dup-1",
                    "category": "normal",
                    "stress_vector": "BASELINE_VALID_INPUT",
                    "expected_handling": "SUCCESS",
                    "status": "PASSED",
                }
            ],
        }
        res = client.post(f"/api/v1/workflows/{wf_id}/regression/compare", json=payload)
        assert res.status_code == 400
        assert "Duplicate scenario_id" in res.json()["detail"]
    finally:
        client.delete(f"/api/v1/workflows/{wf_id}")


def test_regression_compare_endpoint_mismatched_workflow_id():
    wf_id = _create_persisted_workflow()
    try:
        payload = {
            "baseline": {
                "workflow_id": "different-workflow-id",
                "workflow_version": "1.0.0",
                "tested_at": datetime.now(timezone.utc).isoformat(),
                "baseline_results": [
                    {
                        "scenario_id": "s1",
                        "category": "normal",
                        "stress_vector": "BASELINE_VALID_INPUT",
                        "sample_input": {"input": "hello"},
                        "expected_handling": "SUCCESS",
                        "status": "FAILED",
                    }
                ],
            },
            "post_repair_results": [
                {
                    "scenario_id": "s1",
                    "category": "normal",
                    "stress_vector": "BASELINE_VALID_INPUT",
                    "expected_handling": "SUCCESS",
                    "status": "PASSED",
                }
            ],
        }
        res = client.post(f"/api/v1/workflows/{wf_id}/regression/compare", json=payload)
        assert res.status_code == 400
        detail = res.json()["detail"]
        assert "Workflow ID mismatch" in detail
        assert wf_id in detail
        assert "different-workflow-id" in detail
    finally:
        client.delete(f"/api/v1/workflows/{wf_id}")
