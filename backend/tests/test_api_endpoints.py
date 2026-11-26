import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.execution import ExecutionStatus

client = TestClient(app)


def test_create_and_execute_workflow_via_api():
    workflow_payload = {
        "name": "Integration Test Workflow",
        "description": "Verifying API execution pipeline",
        "version": "1.0.0",
        "configuration": {
            "timeoutSeconds": 300,
            "maxRetries": 1,
            "autoRepairEnabled": True,
            "executionMode": "langgraph",
        },
        "nodes": [
            {
                "id": "node_in",
                "type": "Input",
                "name": "User Query",
                "position": {"x": 100, "y": 100},
                "config": {"required": True},
            },
            {
                "id": "node_tool",
                "type": "Tool",
                "name": "Text Transformer",
                "position": {"x": 300, "y": 100},
                "config": {"toolName": "text_formatter", "operation": "upper"},
            },
            {
                "id": "node_out",
                "type": "Output",
                "name": "Final Result",
                "position": {"x": 500, "y": 100},
                "config": {"outputFormat": "json"},
            },
        ],
        "edges": [
            {"id": "e1", "source": "node_in", "target": "node_tool"},
            {"id": "e2", "source": "node_tool", "target": "node_out"},
        ],
        "tags": ["integration", "testing"],
    }

    # 1. Create workflow
    create_resp = client.post("/api/v1/workflows", json=workflow_payload)
    assert create_resp.status_code == 201
    created_wf = create_resp.json()
    wf_id = created_wf["id"]

    # 2. Retrieve workflow by ID
    get_resp = client.get(f"/api/v1/workflows/{wf_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Integration Test Workflow"

    # 3. Execute workflow
    exec_resp = client.post(
        f"/api/v1/workflows/{wf_id}/execute",
        json={"inputs": {"node_in": "fastapi integration test"}},
    )
    assert exec_resp.status_code == 200
    report = exec_resp.json()
    assert report["status"] == "SUCCESS"
    assert "FASTAPI INTEGRATION TEST" in str(report["result"])
    exec_id = report["execution_id"]

    # 4. Fetch execution record
    rec_resp = client.get(f"/api/v1/executions/{exec_id}")
    assert rec_resp.status_code == 200
    assert rec_resp.json()["status"] == "SUCCESS"

    # 5. Fetch execution logs
    logs_resp = client.get(f"/api/v1/executions/{exec_id}/logs")
    assert logs_resp.status_code == 200
    assert len(logs_resp.json()) == 3


def test_ad_hoc_execution_run_endpoint():
    ad_hoc_payload = {
        "workflow": {
            "id": "ad_hoc_calc",
            "nodes": [
                {"id": "n1", "type": "Input", "name": "Input", "config": {}},
                {"id": "n2", "type": "Tool", "name": "Calculator", "config": {"toolName": "calculator"}},
                {"id": "n3", "type": "Output", "name": "Output", "config": {}},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ],
        },
        "inputs": {"n1": {"expression": "25 * 4"}},
    }

    resp = client.post("/api/v1/executions/run", json=ad_hoc_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["result"]["result"]["result"] == 100.0


def test_human_approval_api_flow():
    workflow_payload = {
        "name": "Approval Flow Workflow",
        "description": "Approval test",
        "version": "1.0.0",
        "nodes": [
            {"id": "n1", "type": "Input", "name": "Draft Contract", "position": {"x": 0, "y": 0}, "config": {}},
            {"id": "n2", "type": "Human Approval", "name": "Legal Signoff", "position": {"x": 200, "y": 0}, "config": {}},
            {"id": "n3", "type": "Output", "name": "Signed Contract", "position": {"x": 400, "y": 0}, "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
        ],
    }

    create_resp = client.post("/api/v1/workflows", json=workflow_payload)
    wf_id = create_resp.json()["id"]

    # Trigger execution - should pause at Human Approval
    exec_resp = client.post(
        f"/api/v1/workflows/{wf_id}/execute",
        json={"inputs": {"n1": "Standard Agreement v2"}},
    )
    assert exec_resp.status_code == 200
    report = exec_resp.json()
    assert report["status"] == "WAITING_FOR_APPROVAL"
    assert report["waiting_node_id"] == "n2"
    exec_id = report["execution_id"]

    # Approve execution
    approve_resp = client.post(
        f"/api/v1/executions/{exec_id}/approve",
        json={"comment": "Approved by Legal Counsel"},
    )
    assert approve_resp.status_code == 200
    resumed = approve_resp.json()
    assert resumed["status"] == "SUCCESS"


def test_human_rejection_api_flow():
    workflow_payload = {
        "name": "Rejection Flow Workflow",
        "description": "Rejection test",
        "version": "1.0.0",
        "nodes": [
            {"id": "n1", "type": "Input", "name": "Payment Request", "position": {"x": 0, "y": 0}, "config": {}},
            {"id": "n2", "type": "Human Approval", "name": "Finance Approval", "position": {"x": 200, "y": 0}, "config": {}},
            {"id": "n3", "type": "Output", "name": "Payment Confirmation", "position": {"x": 400, "y": 0}, "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
        ],
    }

    create_resp = client.post("/api/v1/workflows", json=workflow_payload)
    wf_id = create_resp.json()["id"]

    exec_resp = client.post(
        f"/api/v1/workflows/{wf_id}/execute",
        json={"inputs": {"n1": {"amount": 50000, "vendor": "ACME Corp"}}},
    )
    assert exec_resp.status_code == 200
    report = exec_resp.json()
    assert report["status"] == "WAITING_FOR_APPROVAL"
    exec_id = report["execution_id"]

    # Reject execution
    reject_resp = client.post(
        f"/api/v1/executions/{exec_id}/reject",
        json={"comment": "Invoice exceeds budget limit"},
    )
    assert reject_resp.status_code == 200
    rejected = reject_resp.json()
    assert rejected["status"] == "REJECTED"
    assert "rejected" in str(rejected["error_message"]).lower()

    # Verify status via GET /executions/{id}
    status_resp = client.get(f"/api/v1/executions/{exec_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "REJECTED"
