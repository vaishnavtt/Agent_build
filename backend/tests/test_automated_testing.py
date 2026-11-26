import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_workflow(input_type="text", required=True, description="Summarize customer tickets.", valid=True):
    nodes = [
        {
            "id": "input-1",
            "type": "customWorkflow",
            "data": {
                "label": "Workflow Input",
                "componentType": "Input",
                "config": {
                    "inputType": input_type,
                    "required": required,
                },
            },
        },
        {
            "id": "llm-1",
            "type": "customWorkflow",
            "data": {
                "label": "AI Model (Gemini)",
                "componentType": "LLM",
                "config": {
                    "model": "gemini-1.5-pro",
                    "systemPrompt": "Process the input accurately." if valid else "",
                    "temperature": 0.5,
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
            "id": "edge-1",
            "source": "input-1",
            "target": "llm-1",
            "sourceHandle": "output",
            "targetHandle": "prompt",
        },
        {
            "id": "edge-2",
            "source": "llm-1",
            "target": "output-1",
            "sourceHandle": "response",
            "targetHandle": "input",
        },
    ]
    payload = {
        "name": f"Test Gen Workflow ({input_type})",
        "description": description,
        "version": "1.0.0",
        "nodes": nodes,
        "edges": edges,
        "tags": ["test-gen"],
    }
    res = client.post("/api/v1/workflows", json=payload)
    assert res.status_code == 201
    return res.json()["id"]


def test_generate_tests_text_input_all_categories_and_structure():
    wf_id = _create_workflow(input_type="text", required=True)
    try:
        res = client.post(f"/api/v1/workflows/{wf_id}/tests/generate", json={})
        assert res.status_code == 200
        body = res.json()

        assert body["workflow_id"] == wf_id
        assert body["input_type_detected"] == "text"
        assert body["input_required"] is True
        assert body["validation_passed"] is True
        assert body["validation_readiness_score"] == 100
        assert body["requirement_used"] == "Summarize customer tickets."
        assert body["total_tests"] == len(body["test_cases"])
        assert body["total_tests"] >= 3

        categories = {tc["category"] for tc in body["test_cases"]}
        assert categories == {"normal", "invalid", "edge"}

        for tc in body["test_cases"]:
            assert set(tc.keys()) >= {
                "test_case_id",
                "name",
                "description",
                "category",
                "sample_input",
                "expected_behavior",
                "status",
            }
            assert tc["status"] == "NOT_RUN"
            assert isinstance(tc["sample_input"], dict)

        normal_cases = [tc for tc in body["test_cases"] if tc["category"] == "normal"]
        assert isinstance(normal_cases[0]["sample_input"]["input"], str)
    finally:
        client.delete(f"/api/v1/workflows/{wf_id}")


def test_generate_tests_json_input_type():
    wf_id = _create_workflow(input_type="json", required=True)
    try:
        res = client.post(f"/api/v1/workflows/{wf_id}/tests/generate")
        assert res.status_code == 200
        body = res.json()
        assert body["input_type_detected"] == "json"

        normal_cases = [tc for tc in body["test_cases"] if tc["category"] == "normal"]
        assert isinstance(normal_cases[0]["sample_input"]["input"], dict)

        invalid_cases = [tc for tc in body["test_cases"] if tc["category"] == "invalid"]
        assert any("JSON" in tc["name"] or "Malformed" in tc["name"] for tc in invalid_cases)
    finally:
        client.delete(f"/api/v1/workflows/{wf_id}")


def test_generate_tests_file_url_input_type():
    wf_id = _create_workflow(input_type="file_url", required=True)
    try:
        res = client.post(f"/api/v1/workflows/{wf_id}/tests/generate")
        assert res.status_code == 200
        body = res.json()
        assert body["input_type_detected"] == "file_url"

        normal_cases = [tc for tc in body["test_cases"] if tc["category"] == "normal"]
        assert normal_cases[0]["sample_input"]["input"].startswith("https://")
    finally:
        client.delete(f"/api/v1/workflows/{wf_id}")


def test_generate_tests_optional_input():
    wf_id = _create_workflow(input_type="text", required=False)
    try:
        res = client.post(f"/api/v1/workflows/{wf_id}/tests/generate")
        assert res.status_code == 200
        body = res.json()
        assert body["input_required"] is False

        normal_cases = [tc for tc in body["test_cases"] if tc["category"] == "normal"]
        assert any(tc["sample_input"] == {} for tc in normal_cases)

        invalid_cases = [tc for tc in body["test_cases"] if tc["category"] == "invalid"]
        assert not any(tc["name"] == "Empty Required Input" for tc in invalid_cases)
    finally:
        client.delete(f"/api/v1/workflows/{wf_id}")


def test_generate_tests_empty_description_fallback():
    wf_id = _create_workflow(input_type="text", required=True, description="")
    try:
        res = client.post(f"/api/v1/workflows/{wf_id}/tests/generate")
        assert res.status_code == 200
        body = res.json()
        assert "Inferred requirement" in body["requirement_used"]
        assert body["total_tests"] >= 3
        assert all(tc["status"] == "NOT_RUN" for tc in body["test_cases"])
    finally:
        client.delete(f"/api/v1/workflows/{wf_id}")


def test_generate_tests_requirement_override():
    wf_id = _create_workflow(input_type="text", required=True, description="Old requirement")
    try:
        override_text = "Extract invoice total and tax amount from receipt text."
        res = client.post(
            f"/api/v1/workflows/{wf_id}/tests/generate",
            json={"requirement": override_text},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["requirement_used"] == override_text
        normal_cases = [tc for tc in body["test_cases"] if tc["category"] == "normal"]
        assert override_text[:40] in normal_cases[0]["sample_input"]["input"]
    finally:
        client.delete(f"/api/v1/workflows/{wf_id}")


def test_generate_tests_invalid_workflow_returns_400():
    wf_id = _create_workflow(input_type="text", required=True, valid=False)
    try:
        res = client.post(f"/api/v1/workflows/{wf_id}/tests/generate")
        assert res.status_code == 400
        detail = res.json()["detail"]
        assert "validation_errors" in detail
        assert any(e["issue_type"] == "MISSING_LLM_PROMPT" for e in detail["validation_errors"])
    finally:
        client.delete(f"/api/v1/workflows/{wf_id}")


def test_generate_tests_nonexistent_workflow_returns_404():
    res = client.post("/api/v1/workflows/does-not-exist-999/tests/generate")
    assert res.status_code == 404
