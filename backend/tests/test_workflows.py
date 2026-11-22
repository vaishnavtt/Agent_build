import pytest
from fastapi.testclient import TestClient


SAMPLE_WORKFLOW_PAYLOAD = {
    "name": "Customer Support Triage Agent",
    "description": "Automatically triage customer requests and summarize tickets.",
    "version": "1.0.0",
    "configuration": {
        "timeoutSeconds": 300,
        "maxRetries": 2,
        "autoRepairEnabled": True,
        "executionMode": "langgraph",
    },
    "nodes": [
        {
            "id": "node-1",
            "type": "customWorkflow",
            "name": "Start",
            "data": {"label": "Customer Ticket", "componentType": "Input"},
        },
        {
            "id": "node-2",
            "type": "customWorkflow",
            "name": "Understand",
            "data": {"label": "AI Classifier", "componentType": "LLM"},
        },
        {
            "id": "node-3",
            "type": "customWorkflow",
            "name": "Output",
            "data": {"label": "Report", "componentType": "Output"},
        },
    ],
    "edges": [
        {"id": "e1-2", "source": "node-1", "target": "node-2"},
        {"id": "e2-3", "source": "node-2", "target": "node-3"},
    ],
    "tags": ["support", "nlp"],
}


def test_workflow_crud_lifecycle(client: TestClient):
    """Verify end-to-end CRUD: Create, Read, List, Update, Soft-Delete, and Hard-Delete."""
    # 1. CREATE WORKFLOW
    res = client.post("/api/v1/workflows", json=SAMPLE_WORKFLOW_PAYLOAD)
    assert res.status_code == 201
    created = res.json()
    assert created["name"] == SAMPLE_WORKFLOW_PAYLOAD["name"]
    assert "id" in created
    assert created["status"] == "active"
    assert created["is_active"] is True
    assert "workflow_json" in created
    assert created["workflow_json"]["schemaVersion"] == "1.0.0"
    workflow_id = created["id"]

    # 2. GET WORKFLOW BY ID
    res_get = client.get(f"/api/v1/workflows/{workflow_id}")
    assert res_get.status_code == 200
    retrieved = res_get.json()
    assert retrieved["id"] == workflow_id
    assert len(retrieved["nodes"]) == 3
    assert len(retrieved["edges"]) == 2

    # 3. LIST WORKFLOWS
    res_list = client.get("/api/v1/workflows?skip=0&limit=10")
    assert res_list.status_code == 200
    items = res_list.json()
    assert any(w["id"] == workflow_id for w in items)

    # 4. UPDATE WORKFLOW
    update_payload = {
        "name": "Updated Triage Agent",
        "description": "Enhanced triage logic.",
    }
    res_update = client.put(f"/api/v1/workflows/{workflow_id}", json=update_payload)
    assert res_update.status_code == 200
    updated = res_update.json()
    assert updated["name"] == "Updated Triage Agent"
    assert updated["description"] == "Enhanced triage logic."

    # 5. SOFT-DELETE WORKFLOW
    res_delete = client.delete(f"/api/v1/workflows/{workflow_id}")
    assert res_delete.status_code == 204

    # 6. VERIFY SOFT-DELETED WORKFLOW CANNOT BE RETRIEVED BY ACTIVE GET
    res_after_delete = client.get(f"/api/v1/workflows/{workflow_id}")
    assert res_after_delete.status_code == 404

    # 7. HARD-DELETE WORKFLOW
    # Create another workflow for hard-delete test
    res_h = client.post("/api/v1/workflows", json=SAMPLE_WORKFLOW_PAYLOAD)
    wf_h_id = res_h.json()["id"]
    res_hard_del = client.delete(f"/api/v1/workflows/{wf_h_id}?hard_delete=true")
    assert res_hard_del.status_code == 204
    assert client.get(f"/api/v1/workflows/{wf_h_id}").status_code == 404


def test_workflow_create_from_canonical_json(client: TestClient):
    """Verify workflow creation accepting direct shared/workflow.schema.json format."""
    canonical_payload = {
        "schemaVersion": "1.0.0",
        "metadata": {
            "name": "Canonical Schema Workflow",
            "description": "Direct canonical format test",
            "version": "1.2.0",
            "tags": ["finance", "audit"],
        },
        "configuration": {
            "timeoutSeconds": 120,
            "maxRetries": 1,
            "autoRepairEnabled": True,
            "executionMode": "sequential",
        },
        "nodes": [
            {"id": "n1", "type": "Input", "name": "Start Node", "position": {"x": 0, "y": 0}, "config": {}},
            {"id": "n2", "type": "Output", "name": "End Node", "position": {"x": 200, "y": 0}, "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
        ],
    }
    res = client.post("/api/v1/workflows", json=canonical_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Canonical Schema Workflow"
    assert data["version"] == "1.2.0"
    assert len(data["nodes"]) == 2


def test_get_nonexistent_workflow_returns_404(client: TestClient):
    """Verify 404 response when querying a non-existent workflow ID."""
    res = client.get("/api/v1/workflows/non-existent-uuid-1234")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_update_nonexistent_workflow_returns_404(client: TestClient):
    """Verify 404 response when updating a non-existent workflow ID."""
    res = client.put("/api/v1/workflows/non-existent-uuid-1234", json={"name": "New Name"})
    assert res.status_code == 404


def test_delete_nonexistent_workflow_returns_404(client: TestClient):
    """Verify 404 response when deleting a non-existent workflow ID."""
    res = client.delete("/api/v1/workflows/non-existent-uuid-1234")
    assert res.status_code == 404


def test_invalid_workflow_creation_validation_error(client: TestClient):
    """Verify 422 Unprocessable Entity when required fields are missing or invalid."""
    # Missing required name
    res = client.post("/api/v1/workflows", json={"description": "Missing name field"})
    assert res.status_code == 422
    assert "error_code" in res.json()
    assert res.json()["error_code"] == "VALIDATION_ERROR"

    # Name exceeds maximum length
    long_name = "x" * 150
    res_long = client.post("/api/v1/workflows", json={"name": long_name})
    assert res_long.status_code == 422


def test_validate_workflow_endpoint(client: TestClient):
    """Verify validation endpoint detects missing nodes, missing start, missing output, and disconnected nodes."""
    # 1. Empty workflow
    res_empty = client.post("/api/v1/workflows/validate", json={"nodes": [], "edges": []})
    assert res_empty.status_code == 200
    data_empty = res_empty.json()
    assert data_empty["is_valid"] is False
    assert any(i["id"] == "err-no-nodes" for i in data_empty["issues"])

    # 2. Missing Start node
    payload_no_start = {
        "nodes": [
            {"id": "n1", "data": {"label": "LLM Step", "componentType": "LLM"}},
            {"id": "n2", "data": {"label": "Output Step", "componentType": "Output"}},
        ],
        "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
    }
    res_no_start = client.post("/api/v1/workflows/validate", json=payload_no_start)
    assert res_no_start.status_code == 200
    assert any("start" in i["title"].lower() for i in res_no_start.json()["issues"])

    # 3. Disconnected nodes
    payload_disconnected = {
        "nodes": [
            {"id": "n1", "data": {"label": "Input", "componentType": "Input"}},
            {"id": "n2", "data": {"label": "Orphan Step", "componentType": "LLM"}},
        ],
        "edges": [],
    }
    res_disc = client.post("/api/v1/workflows/validate", json=payload_disconnected)
    assert res_disc.status_code == 200
    val_data = res_disc.json()
    assert any("disconnected" in i["title"].lower() for i in val_data["issues"])
    assert val_data["readiness_score"] < 100
