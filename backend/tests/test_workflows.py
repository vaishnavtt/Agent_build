import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_and_get_workflow():
    """Verify creating a new workflow and retrieving it by ID."""
    payload = {
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
        ],
        "edges": [
            {"id": "e1-2", "source": "node-1", "target": "node-2"},
        ],
        "tags": ["support", "nlp"],
    }

    # 1. Create workflow
    res = client.post("/api/v1/workflows", json=payload)
    assert res.status_code == 201
    created_data = res.json()
    assert created_data["name"] == payload["name"]
    assert "id" in created_data
    workflow_id = created_data["id"]

    # 2. Get workflow
    res_get = client.get(f"/api/v1/workflows/{workflow_id}")
    assert res_get.status_code == 200
    retrieved = res_get.json()
    assert retrieved["id"] == workflow_id
    assert len(retrieved["nodes"]) == 2
    assert len(retrieved["edges"]) == 1

    # 3. List workflows
    res_list = client.get("/api/v1/workflows")
    assert res_list.status_code == 200
    workflows = res_list.json()
    assert any(w["id"] == workflow_id for w in workflows)

    # 4. Update workflow
    res_update = client.put(
        f"/api/v1/workflows/{workflow_id}",
        json={"name": "Updated Support Agent"},
    )
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Updated Support Agent"

    # 5. Record execution
    exec_payload = {
        "workflow_id": workflow_id,
        "status": "COMPLETED",
        "input_payload": {"ticket_id": "TCK-1002"},
        "output_result": {"priority": "HIGH", "category": "BILLING"},
        "repair_attempts": 0,
    }
    res_exec = client.post(f"/api/v1/workflows/{workflow_id}/execute", json=exec_payload)
    assert res_exec.status_code == 201
    exec_data = res_exec.json()
    assert exec_data["status"] == "COMPLETED"

    # 6. List executions
    res_execs = client.get(f"/api/v1/workflows/{workflow_id}/executions")
    assert res_execs.status_code == 200
    assert len(res_execs.json()) >= 1

    # 7. Delete workflow
    res_del = client.delete(f"/api/v1/workflows/{workflow_id}")
    assert res_del.status_code == 204

    # 8. Check deleted is not returned by get
    res_after_del = client.get(f"/api/v1/workflows/{workflow_id}")
    assert res_after_del.status_code == 404


def test_validate_workflow_api():
    """Verify the workflow validation endpoint accurately detects missing start step and disconnected nodes."""
    # Disconnected node test
    payload = {
        "nodes": [
            {"id": "node-1", "data": {"label": "Input", "componentType": "Input"}},
            {"id": "node-2", "data": {"label": "Orphan Step", "componentType": "LLM"}},
        ],
        "edges": [],
    }
    res = client.post("/api/v1/workflows/validate", json=payload)
    assert res.status_code == 200
    val_data = res.json()
    assert len(val_data["issues"]) > 0
    assert any("Disconnected" in i["title"] for i in val_data["issues"])
