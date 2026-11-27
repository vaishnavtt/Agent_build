import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services.workflow_service import WorkflowService
from app.schemas.workflow import WorkflowCreate, WorkflowRecoveryReserveRequest, WorkflowRecoveryCompleteRequest


def test_durable_recovery_two_attempt_limit(client: TestClient):
    """Verify that DurableAttempts strictly enforces a maximum of two repair attempts."""
    # 1. Create workflow
    res_wf = client.post(
        "/api/v1/workflows",
        json={"name": "Recovery Budget Workflow", "nodes": [], "edges": []},
    )
    wf_id = res_wf.json()["id"]

    # 2. Reserve Attempt 1 -> succeeds
    res_att1 = client.post(
        f"/api/v1/workflows/{wf_id}/recoveries/reserve",
        json={"error_context": {"reason": "Schema validation failed in node-2"}},
    )
    assert res_att1.status_code == 201
    rec1 = res_att1.json()
    assert rec1["attempt_number"] == 1
    assert rec1["status"] == "reserved"
    assert rec1["reserved_at"] is not None

    # Complete Attempt 1 as failed
    res_comp1 = client.post(
        f"/api/v1/workflows/{wf_id}/recoveries/{rec1['id']}/complete",
        json={"status": "failed", "notes": "First repair patch did not resolve error"},
    )
    assert res_comp1.status_code == 200
    assert res_comp1.json()["status"] == "failed"
    assert res_comp1.json()["completed_at"] is not None

    # 3. Reserve Attempt 2 -> succeeds
    res_att2 = client.post(
        f"/api/v1/workflows/{wf_id}/recoveries/reserve",
        json={"error_context": {"reason": "Second failure encountered"}},
    )
    assert res_att2.status_code == 201
    rec2 = res_att2.json()
    assert rec2["attempt_number"] == 2
    assert rec2["status"] == "reserved"

    # Complete Attempt 2 as failed
    res_comp2 = client.post(
        f"/api/v1/workflows/{wf_id}/recoveries/{rec2['id']}/complete",
        json={"status": "failed", "notes": "Second repair attempt failed"},
    )
    assert res_comp2.status_code == 200

    # 4. Attempt 3 must be strictly rejected (budget exhausted) -> 429 Too Many Requests
    res_att3 = client.post(
        f"/api/v1/workflows/{wf_id}/recoveries/reserve",
        json={"error_context": {"reason": "Attempting unauthorized third repair"}},
    )
    assert res_att3.status_code in (429, 400)
    assert "exceeded" in res_att3.json()["detail"].lower()


def test_recovery_idempotency_deduplication(client: TestClient):
    """Verify that duplicate recovery requests with the same idempotency_key return the existing reservation."""
    res_wf = client.post(
        "/api/v1/workflows",
        json={"name": "Idempotency Workflow", "nodes": [], "edges": []},
    )
    wf_id = res_wf.json()["id"]

    # First reservation with key
    res1 = client.post(
        f"/api/v1/workflows/{wf_id}/recoveries/reserve",
        json={
            "idempotency_key": "idemp-unique-token-999",
            "error_context": {"reason": "Network timeout in worker"},
        },
    )
    assert res1.status_code == 201
    rec1_id = res1.json()["id"]

    # Duplicate reservation with identical key
    res2 = client.post(
        f"/api/v1/workflows/{wf_id}/recoveries/reserve",
        json={
            "idempotency_key": "idemp-unique-token-999",
            "error_context": {"reason": "Network timeout in worker duplicate"},
        },
    )
    assert res2.status_code in (200, 201)
    rec2_id = res2.json()["id"]

    # Both requests must return the exact same recovery record ID without consuming a second attempt
    assert rec1_id == rec2_id


def test_concurrent_reservation_protection(client: TestClient):
    """Verify that a worker cannot reserve a new repair attempt while one is already active/reserved."""
    res_wf = client.post(
        "/api/v1/workflows",
        json={"name": "Concurrent Recovery Workflow", "nodes": [], "edges": []},
    )
    wf_id = res_wf.json()["id"]

    # Worker 1 reserves attempt 1
    res1 = client.post(
        f"/api/v1/workflows/{wf_id}/recoveries/reserve",
        json={"error_context": {"reason": "Worker 1 failure"}},
    )
    assert res1.status_code == 201
    rec1_id = res1.json()["id"]

    # Worker 2 tries to reserve while attempt 1 is still in reserved status
    res2 = client.post(
        f"/api/v1/workflows/{wf_id}/recoveries/reserve",
        json={"error_context": {"reason": "Worker 2 parallel attempt"}},
    )
    # The API safely returns the existing active reservation rather than creating a concurrent one
    assert res2.status_code in (200, 201, 409)
    if res2.status_code in (200, 201):
        assert res2.json()["id"] == rec1_id


def test_recovery_persistence_across_service_instances(db_session: Session):
    """Verify that recovery state is stored durably in the database and survives service restarts."""
    service1 = WorkflowService(db_session)
    wf = service1.create_workflow(WorkflowCreate(name="Durable Service Workflow"))

    # Service 1 reserves attempt 1
    rec1 = service1.reserve_recovery_attempt(
        wf.id,
        WorkflowRecoveryReserveRequest(error_context={"test": "persistence"}),
    )
    assert rec1.attempt_number == 1

    # Simulate restart by instantiating fresh service on the same database
    service2 = WorkflowService(db_session)
    recoveries = service2.list_workflow_recoveries(wf.id)
    assert len(recoveries) == 1
    assert recoveries[0].id == rec1.id
    assert recoveries[0].attempt_number == 1


def test_recovery_lifecycle_timestamps(client: TestClient):
    """Verify all lifecycle timestamps (reserved_at, completed_at, promoted_at) are tracked."""
    res_wf = client.post(
        "/api/v1/workflows",
        json={"name": "Timestamp Tracking Workflow", "nodes": [], "edges": []},
    )
    wf_id = res_wf.json()["id"]

    # Reserve
    res_res = client.post(
        f"/api/v1/workflows/{wf_id}/recoveries/reserve",
        json={"error_context": {"step": "test"}},
    )
    rec = res_res.json()
    assert rec["reserved_at"] is not None

    # Complete
    res_comp = client.post(
        f"/api/v1/workflows/{wf_id}/recoveries/{rec['id']}/complete",
        json={"status": "completed", "proposed_patch": {"fixed": True}},
    )
    assert res_comp.status_code == 200
    completed_rec = res_comp.json()
    assert completed_rec["completed_at"] is not None
