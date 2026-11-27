import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def sample_workflow_id(client: TestClient) -> str:
    """Create a temporary workflow to attach executions to."""
    payload = {
        "name": "Execution Test Workflow",
        "description": "Workflow for testing execution telemetry.",
        "nodes": [
            {"id": "n1", "data": {"label": "Start", "componentType": "Input"}},
            {"id": "n2", "data": {"label": "Output", "componentType": "Output"}},
        ],
        "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
    }
    res = client.post("/api/v1/workflows", json=payload)
    assert res.status_code == 201
    return res.json()["id"]


def test_create_and_get_execution_record(client: TestClient, sample_workflow_id: str):
    """Verify creating an execution record and fetching it by ID."""
    payload = {
        "workflow_id": sample_workflow_id,
        "status": "pending",
        "input_data": {"user_query": "Test query payload"},
        "repair_attempts": 0,
    }

    # 1. Create execution
    res = client.post(f"/api/v1/workflows/{sample_workflow_id}/executions", json=payload)
    assert res.status_code == 201
    created = res.json()
    assert "id" in created
    assert created["workflow_id"] == sample_workflow_id
    assert created["status"] == "pending"
    assert created["input_data"] == payload["input_data"]
    assert created["input_payload"] == payload["input_data"]  # compatibility check
    execution_id = created["id"]

    # 2. Retrieve execution by unique ID via GET /api/v1/executions/{execution_id}
    res_get = client.get(f"/api/v1/executions/{execution_id}")
    assert res_get.status_code == 200
    retrieved = res_get.json()
    assert retrieved["id"] == execution_id
    assert retrieved["workflow_id"] == sample_workflow_id
    assert retrieved["status"] == "pending"


def test_legacy_execute_alias_endpoint(client: TestClient, sample_workflow_id: str):
    """Verify backward compatibility of POST /api/v1/workflows/{id}/execute endpoint."""
    payload = {
        "workflow_id": sample_workflow_id,
        "status": "COMPLETED",
        "input_payload": {"ticket_id": "TCK-1002"},
        "output_result": {"priority": "HIGH", "category": "BILLING"},
        "repair_attempts": 1,
    }
    res = client.post(f"/api/v1/workflows/{sample_workflow_id}/execute", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "completed"
    assert data["input_data"] == {"ticket_id": "TCK-1002"}
    assert data["output_data"] == {"priority": "HIGH", "category": "BILLING"}
    assert data["repair_attempts"] == 1


def test_patch_execution_record(client: TestClient, sample_workflow_id: str):
    """Verify PATCH /api/v1/executions/{execution_id} status transition and result update."""
    # 1. Create initial pending execution
    create_res = client.post(
        f"/api/v1/workflows/{sample_workflow_id}/executions",
        json={"status": "pending", "input_data": {"query": "Search query"}},
    )
    assert create_res.status_code == 201
    exec_id = create_res.json()["id"]

    # 2. Update to running
    patch_running = client.patch(
        f"/api/v1/executions/{exec_id}",
        json={"status": "running"},
    )
    assert patch_running.status_code == 200
    assert patch_running.json()["status"] == "running"

    # 3. Complete execution with output and duration
    patch_completed = client.patch(
        f"/api/v1/executions/{exec_id}",
        json={
            "status": "completed",
            "output_data": {"result": "Successfully processed"},
            "execution_duration": 1.45,
        },
    )
    assert patch_completed.status_code == 200
    completed_data = patch_completed.json()
    assert completed_data["status"] == "completed"
    assert completed_data["output_data"] == {"result": "Successfully processed"}
    assert completed_data["execution_duration"] == 1.45
    assert completed_data["completed_at"] is not None


def test_list_workflow_executions_history(client: TestClient, sample_workflow_id: str):
    """Verify listing execution history for a specific workflow and filtering by status."""
    # Create 3 executions with different statuses
    for status_val in ["completed", "failed", "pending"]:
        client.post(
            f"/api/v1/workflows/{sample_workflow_id}/executions",
            json={"status": status_val, "input_data": {"val": status_val}},
        )

    # List all executions for workflow
    res_list = client.get(f"/api/v1/workflows/{sample_workflow_id}/executions")
    assert res_list.status_code == 200
    history = res_list.json()
    assert len(history) >= 3

    # Filter by status
    res_filtered = client.get(f"/api/v1/workflows/{sample_workflow_id}/executions?status=failed")
    assert res_filtered.status_code == 200
    failed_items = res_filtered.json()
    assert all(item["status"] == "failed" for item in failed_items)


def test_execution_telemetry_persistence(client: TestClient, sample_workflow_id: str):
    """Verify rich telemetry fields (node logs, tokens, cost, provider, model) are persisted."""
    telemetry_payload = {
        "workflow_id": sample_workflow_id,
        "status": "completed",
        "input_data": {"query": "Translate English to French"},
        "output_data": {"translation": "Bonjour le monde"},
        "node_logs": [
            {"node": "n1", "level": "INFO", "message": "Input received"},
            {"node": "n2", "level": "INFO", "message": "Model invoked successfully"},
        ],
        "token_usage": {
            "prompt_tokens": 120,
            "completion_tokens": 45,
            "total_tokens": 165,
        },
        "ai_provider": "google",
        "ai_model": "gemini-1.5-pro",
        "estimated_cost": 0.00035,
        "execution_duration": 1.25,
    }

    res = client.post(f"/api/v1/workflows/{sample_workflow_id}/executions", json=telemetry_payload)
    assert res.status_code == 201
    created = res.json()
    exec_id = created["id"]

    assert created["node_logs"] == telemetry_payload["node_logs"]
    assert created["token_usage"] == telemetry_payload["token_usage"]
    assert created["ai_provider"] == "google"
    assert created["ai_model"] == "gemini-1.5-pro"
    assert created["estimated_cost"] == 0.00035

    # Retrieve and verify stored record
    get_res = client.get(f"/api/v1/executions/{exec_id}")
    assert get_res.status_code == 200
    stored = get_res.json()
    assert stored["ai_provider"] == "google"
    assert stored["token_usage"]["total_tokens"] == 165


def test_execution_status_case_insensitivity(client: TestClient, sample_workflow_id: str):
    """Verify that execution status filters work case-insensitively (e.g. COMPLETED vs completed)."""
    client.post(
        f"/api/v1/workflows/{sample_workflow_id}/executions",
        json={"status": "completed", "input_data": {"flag": "upper_test"}},
    )

    # Filter using uppercase "COMPLETED"
    res_upper = client.get(f"/api/v1/workflows/{sample_workflow_id}/executions?status=COMPLETED")
    assert res_upper.status_code == 200
    assert len(res_upper.json()) >= 1
    assert all(item["status"] == "completed" for item in res_upper.json())

    # Filter using lowercase "completed"
    res_lower = client.get(f"/api/v1/workflows/{sample_workflow_id}/executions?status=completed")
    assert res_lower.status_code == 200
    assert len(res_lower.json()) >= 1


def test_revision_scoped_execution_query(client: TestClient, sample_workflow_id: str):
    """Verify filtering executions by associated workflow revision_id."""
    # Fetch active revision ID of workflow
    wf_res = client.get(f"/api/v1/workflows/{sample_workflow_id}")
    active_rev_id = wf_res.json()["active_revision_id"]

    # Create execution tied to that revision
    client.post(
        f"/api/v1/workflows/{sample_workflow_id}/executions",
        json={"status": "completed", "revision_id": active_rev_id},
    )

    # Query executions for that specific revision
    res_scoped = client.get(f"/api/v1/workflows/{sample_workflow_id}/executions?revision_id={active_rev_id}")
    assert res_scoped.status_code == 200
    items = res_scoped.json()
    assert len(items) >= 1
    assert all(i["revision_id"] == active_rev_id for i in items)


def test_list_all_executions_endpoint(client: TestClient, sample_workflow_id: str):
    """Verify GET /api/v1/executions across workflows."""
    res = client.get("/api/v1/executions?skip=0&limit=10")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_execution_on_nonexistent_workflow_returns_404(client: TestClient):
    """Verify 404 when attempting to create an execution for a non-existent workflow."""
    res = client.post(
        "/api/v1/workflows/non-existent-wf/executions",
        json={"status": "pending", "input_data": {}},
    )
    assert res.status_code == 404


def test_get_nonexistent_execution_returns_404(client: TestClient):
    """Verify 404 when fetching an execution that does not exist."""
    res = client.get("/api/v1/executions/non-existent-exec-id")
    assert res.status_code == 404
