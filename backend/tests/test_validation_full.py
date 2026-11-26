import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.validation import WorkflowValidator

client = TestClient(app)


def _valid_nodes():
    return [
        {
            "id": "n-input",
            "type": "customWorkflow",
            "data": {
                "label": "User Query",
                "componentType": "Input",
                "config": {"inputType": "text", "required": True},
            },
        },
        {
            "id": "n-llm",
            "type": "customWorkflow",
            "data": {
                "label": "Gemini Assistant",
                "componentType": "LLM",
                "config": {
                    "model": "gemini-1.5-pro",
                    "systemPrompt": "Answer concisely.",
                    "temperature": 0.4,
                },
            },
        },
        {
            "id": "n-output",
            "type": "customWorkflow",
            "data": {
                "label": "Final Output",
                "componentType": "Output",
                "config": {"outputFormat": "markdown"},
            },
        },
    ]


def _valid_edges():
    return [
        {
            "id": "e-1",
            "source": "n-input",
            "target": "n-llm",
            "sourceHandle": "output",
            "targetHandle": "prompt",
        },
        {
            "id": "e-2",
            "source": "n-llm",
            "target": "n-output",
            "sourceHandle": "response",
            "targetHandle": "input",
        },
    ]


def test_valid_workflow():
    validator = WorkflowValidator()
    res = validator.validate(nodes=_valid_nodes(), edges=_valid_edges())
    assert res.is_valid is True
    assert res.readiness_score == 100
    assert res.total_nodes == 3
    assert res.total_connections == 2
    assert len(res.errors) == 0
    assert res.validation_details.has_input_node is True
    assert res.validation_details.has_output_node is True
    assert res.validation_details.has_path_to_output is True


def test_deterministic_readiness_score():
    validator = WorkflowValidator()
    nodes = _valid_nodes()
    edges = _valid_edges()
    first = validator.validate(nodes=nodes, edges=edges)
    second = validator.validate(nodes=nodes, edges=edges)
    assert first.readiness_score == second.readiness_score
    assert first.validation_details.score_breakdown == second.validation_details.score_breakdown


def test_empty_workflow():
    validator = WorkflowValidator()
    res = validator.validate(nodes=[], edges=[])
    assert res.is_valid is False
    assert res.readiness_score == 0
    assert res.total_nodes == 0
    assert any(e.issue_type == "EMPTY_WORKFLOW" for e in res.errors)


def test_disconnected_node():
    validator = WorkflowValidator()
    nodes = _valid_nodes() + [
        {
            "id": "n-orphan",
            "type": "Tool",
            "config": {"toolName": "web_search", "timeoutSeconds": 30},
        }
    ]
    res = validator.validate(nodes=nodes, edges=_valid_edges())
    assert res.is_valid is False
    assert "n-orphan" in res.validation_details.disconnected_node_ids
    assert any(
        e.issue_type == "DISCONNECTED_NODE" and e.affected_node_id == "n-orphan"
        for e in res.errors
    )


def test_unreachable_node():
    validator = WorkflowValidator()
    nodes = _valid_nodes() + [
        {
            "id": "n-tool-1",
            "type": "Tool",
            "config": {"toolName": "web_search", "timeoutSeconds": 30},
        },
        {
            "id": "n-tool-2",
            "type": "Tool",
            "config": {"toolName": "python_interpreter", "timeoutSeconds": 30},
        },
    ]
    edges = _valid_edges() + [
        {
            "id": "e-island",
            "source": "n-tool-1",
            "target": "n-tool-2",
            "sourceHandle": "result",
            "targetHandle": "params",
        }
    ]
    res = validator.validate(nodes=nodes, edges=edges)
    assert res.is_valid is False
    assert "n-tool-1" in res.validation_details.unreachable_node_ids
    assert "n-tool-2" in res.validation_details.unreachable_node_ids
    assert any(e.issue_type == "UNREACHABLE_NODE" for e in res.errors)


def test_missing_llm_prompt():
    validator = WorkflowValidator()
    nodes = _valid_nodes()
    nodes[1]["data"]["config"]["systemPrompt"] = "   "
    res = validator.validate(nodes=nodes, edges=_valid_edges())
    assert res.is_valid is False
    assert any(
        e.issue_type == "MISSING_LLM_PROMPT" and e.affected_node_id == "n-llm"
        for e in res.errors
    )


def test_missing_required_configuration():
    validator = WorkflowValidator()
    nodes = _valid_nodes()
    nodes[0]["data"]["config"]["inputType"] = ""
    nodes[2]["data"]["config"]["outputFormat"] = ""
    res = validator.validate(nodes=nodes, edges=_valid_edges())
    assert res.is_valid is False
    missing_cfg_nodes = {
        e.affected_node_id for e in res.errors if e.issue_type == "MISSING_CONFIGURATION"
    }
    assert "n-input" in missing_cfg_nodes
    assert "n-output" in missing_cfg_nodes


def test_unsupported_node_type():
    validator = WorkflowValidator()
    nodes = _valid_nodes() + [
        {
            "id": "n-bad-type",
            "type": "customWorkflow",
            "data": {"label": "Mystery Block", "componentType": "QuantumProcessor", "config": {}},
        }
    ]
    res = validator.validate(nodes=nodes, edges=_valid_edges())
    assert res.is_valid is False
    assert "n-bad-type" in res.validation_details.unsupported_node_ids
    assert any(
        e.issue_type == "UNSUPPORTED_NODE_TYPE" and e.affected_node_id == "n-bad-type"
        for e in res.errors
    )


def test_invalid_source_node():
    validator = WorkflowValidator()
    edges = _valid_edges() + [
        {"id": "e-bad-src", "source": "nonexistent-src", "target": "n-output"}
    ]
    res = validator.validate(nodes=_valid_nodes(), edges=edges)
    assert res.is_valid is False
    assert any(
        e.issue_type == "INVALID_SOURCE_NODE" and e.affected_connection_id == "e-bad-src"
        for e in res.errors
    )


def test_invalid_target_node():
    validator = WorkflowValidator()
    edges = _valid_edges() + [
        {"id": "e-bad-tgt", "source": "n-input", "target": "nonexistent-tgt"}
    ]
    res = validator.validate(nodes=_valid_nodes(), edges=edges)
    assert res.is_valid is False
    assert any(
        e.issue_type == "INVALID_TARGET_NODE" and e.affected_connection_id == "e-bad-tgt"
        for e in res.errors
    )


def test_invalid_source_handle():
    validator = WorkflowValidator()
    edges = [
        {
            "id": "e-bad-sh",
            "source": "n-input",
            "target": "n-llm",
            "sourceHandle": "invalid_output_port",
            "targetHandle": "prompt",
        },
        _valid_edges()[1],
    ]
    res = validator.validate(nodes=_valid_nodes(), edges=edges)
    assert res.is_valid is False
    assert any(
        e.issue_type == "INVALID_SOURCE_HANDLE" and e.affected_connection_id == "e-bad-sh"
        for e in res.errors
    )


def test_invalid_target_handle():
    validator = WorkflowValidator()
    edges = [
        {
            "id": "e-bad-th",
            "source": "n-input",
            "target": "n-llm",
            "sourceHandle": "output",
            "targetHandle": "nonexistent_input_port",
        },
        _valid_edges()[1],
    ]
    res = validator.validate(nodes=_valid_nodes(), edges=edges)
    assert res.is_valid is False
    assert any(
        e.issue_type == "INVALID_TARGET_HANDLE" and e.affected_connection_id == "e-bad-th"
        for e in res.errors
    )


def test_missing_required_input():
    validator = WorkflowValidator()
    # n-llm has no incoming edge; only n-input -> n-output exists
    edges = [{"id": "e-skip", "source": "n-input", "target": "n-output"}]
    res = validator.validate(nodes=_valid_nodes(), edges=edges)
    assert res.is_valid is False
    assert any(
        e.issue_type == "MISSING_REQUIRED_INPUT" and e.affected_node_id == "n-llm"
        for e in res.errors
    )


def test_missing_required_output():
    validator = WorkflowValidator()
    # n-llm has incoming edge from n-input, but no outgoing edge to n-output
    edges = [{"id": "e-1", "source": "n-input", "target": "n-llm"}]
    res = validator.validate(nodes=_valid_nodes(), edges=edges)
    assert res.is_valid is False
    assert any(
        e.issue_type == "MISSING_REQUIRED_OUTPUT" and e.affected_node_id == "n-llm"
        for e in res.errors
    )


def test_validate_full_endpoint_with_persisted_workflow():
    payload = {
        "name": "Validation Integration Test Agent",
        "description": "Tests /validate-full endpoint",
        "version": "1.0.0",
        "nodes": _valid_nodes(),
        "edges": _valid_edges(),
        "tags": ["test"],
    }
    create_res = client.post("/api/v1/workflows", json=payload)
    assert create_res.status_code == 201
    wf_id = create_res.json()["id"]

    try:
        # 1. Empty request body (no body) -> validates persisted SQLite workflow
        val_res = client.post(f"/api/v1/workflows/{wf_id}/validate-full")
        assert val_res.status_code == 200
        body = val_res.json()
        assert body["workflow_id"] == wf_id
        assert body["is_valid"] is True
        assert body["readiness_score"] == 100
        assert body["total_nodes"] == 3
        assert body["total_connections"] == 2
        assert body["errors"] == []
        assert body["warnings"] == []
        assert body["validation_details"]["has_input_node"] is True
        assert body["validation_details"]["has_output_node"] is True
        assert body["validation_details"]["has_path_to_output"] is True

        # 2. Empty JSON object `{}` (Swagger UI default) -> validates persisted SQLite workflow
        empty_json_res = client.post(f"/api/v1/workflows/{wf_id}/validate-full", json={})
        assert empty_json_res.status_code == 200
        empty_json_body = empty_json_res.json()
        assert empty_json_body["total_nodes"] == 3
        assert empty_json_body["total_connections"] == 2
        assert empty_json_body["is_valid"] is True
        assert empty_json_body["readiness_score"] == 100

        # 3. Direct payload override -> validates supplied nodes and edges
        direct_res = client.post(
            f"/api/v1/workflows/{wf_id}/validate-full",
            json={"nodes": _valid_nodes(), "edges": _valid_edges()},
        )
        assert direct_res.status_code == 200
        direct_body = direct_res.json()
        assert direct_body["total_nodes"] == 3
        assert direct_body["total_connections"] == 2
        assert direct_body["is_valid"] is True
        assert direct_body["readiness_score"] == 100
    finally:
        client.delete(f"/api/v1/workflows/{wf_id}")


def test_validate_full_endpoint_not_found():
    res = client.post("/api/v1/workflows/nonexistent-id-123/validate-full")
    assert res.status_code == 404
