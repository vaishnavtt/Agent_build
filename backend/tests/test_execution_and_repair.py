from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_agents_endpoint():
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6
    agent_names = [a["name"] for a in data]
    assert "Planner Agent" in agent_names
    assert "Research Agent" in agent_names
    assert "Execution Agent" in agent_names
    assert "Validation Agent" in agent_names
    assert "Error Detection Agent" in agent_names
    assert "Self-Repair Agent" in agent_names


def test_plan_workflow_endpoint():
    payload = {"prompt": "Create an invoice processing agent"}
    response = client.post("/api/v1/workflows/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 3


def test_run_adhoc_workflow_endpoint():
    payload = {
        "name": "Test Candidate Screener",
        "nodes": [
            {"id": "n1", "data": {"label": "Start", "componentType": "Input"}},
            {"id": "n2", "data": {"label": "Doc Read", "componentType": "Document Reader"}},
            {"id": "n3", "data": {"label": "AI Screen", "componentType": "LLM", "config": {"instructions": "Screen profile."}}},
            {"id": "n4", "data": {"label": "Finish", "componentType": "Output"}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n3", "target": "n4"},
        ],
        "auto_repair": True,
    }
    response = client.post("/api/v1/workflows/run-adhoc", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["COMPLETED", "REPAIRED"]
    assert len(data["steps"]) == 4
    assert len(data["log_evidence"]) > 0


def test_list_all_executions_endpoint():
    response = client.get("/api/v1/workflows/executions/all")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
