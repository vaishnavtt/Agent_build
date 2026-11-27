import pytest
from fastapi.testclient import TestClient


def test_workflow_creation_creates_initial_revision(client: TestClient):
    """Verify that creating a workflow automatically initializes immutable revision #1."""
    payload = {
        "name": "Revision Base Workflow",
        "description": "Testing initial revision creation.",
        "nodes": [
            {"id": "n1", "type": "Input", "name": "Start", "data": {"label": "Input"}}
        ],
        "edges": [],
    }
    res = client.post("/api/v1/workflows", json=payload)
    assert res.status_code == 201
    wf_data = res.json()
    wf_id = wf_data["id"]

    assert wf_data["active_revision_id"] is not None
    assert wf_data["current_revision_number"] == 1

    # Fetch revisions list
    rev_res = client.get(f"/api/v1/workflows/{wf_id}/revisions")
    assert rev_res.status_code == 200
    revisions = rev_res.json()
    assert len(revisions) == 1
    rev1 = revisions[0]
    assert rev1["id"] == wf_data["active_revision_id"]
    assert rev1["revision_number"] == 1
    assert rev1["is_active"] is True
    assert rev1["is_verified"] is True
    assert "snapshot" in rev1
    assert len(rev1["snapshot"]["nodes"]) == 1


def test_workflow_update_creates_sequential_revisions(client: TestClient):
    """Verify that updating a workflow creates sequential, append-only revisions."""
    # 1. Create initial workflow (rev 1)
    res = client.post(
        "/api/v1/workflows",
        json={
            "name": "Sequential Test",
            "nodes": [{"id": "n1", "name": "Start"}],
            "edges": [],
        },
    )
    wf_id = res.json()["id"]

    # 2. Update workflow (should create rev 2)
    update_res = client.put(
        f"/api/v1/workflows/{wf_id}",
        json={
            "name": "Sequential Test Updated",
            "nodes": [
                {"id": "n1", "name": "Start"},
                {"id": "n2", "name": "Process"},
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        },
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["current_revision_number"] == 2
    assert updated_data["name"] == "Sequential Test Updated"

    # 3. Retrieve all revisions
    rev_res = client.get(f"/api/v1/workflows/{wf_id}/revisions")
    assert rev_res.status_code == 200
    revisions = rev_res.json()
    assert len(revisions) == 2

    # Old revision is now inactive; new revision is active
    rev1 = next(r for r in revisions if r["revision_number"] == 1)
    rev2 = next(r for r in revisions if r["revision_number"] == 2)
    assert rev1["is_active"] is False
    assert rev2["is_active"] is True
    assert len(rev2["snapshot"]["nodes"]) == 2


def test_optimistic_locking_prevents_stale_update(client: TestClient):
    """Verify that updating a workflow with a stale base_revision_number returns 409 Conflict."""
    # Create workflow (rev 1)
    res = client.post(
        "/api/v1/workflows",
        json={"name": "Concurrency Test", "nodes": [], "edges": []},
    )
    wf_id = res.json()["id"]

    # First update succeeds (moves from rev 1 to rev 2)
    res_up1 = client.put(
        f"/api/v1/workflows/{wf_id}",
        json={"name": "First Update", "base_revision_number": 1},
    )
    assert res_up1.status_code == 200
    assert res_up1.json()["current_revision_number"] == 2

    # Stale second update trying to update from base_revision_number=1 -> 409 Conflict
    res_stale = client.put(
        f"/api/v1/workflows/{wf_id}",
        json={"name": "Stale Update", "base_revision_number": 1},
    )
    assert res_stale.status_code == 409
    assert "conflict" in res_stale.json()["detail"].lower()

    # Valid second update with current base_revision_number=2 -> succeeds
    res_valid = client.put(
        f"/api/v1/workflows/{wf_id}",
        json={"name": "Valid Second Update", "base_revision_number": 2},
    )
    assert res_valid.status_code == 200
    assert res_valid.json()["current_revision_number"] == 3


def test_revision_diff(client: TestClient):
    """Verify revision comparison / diff endpoint detects added, removed, and modified elements."""
    # Create workflow with n1 and n2
    res = client.post(
        "/api/v1/workflows",
        json={
            "name": "Diff Test",
            "nodes": [
                {"id": "n1", "name": "Start", "data": {"step": 1}},
                {"id": "n2", "name": "Old Step", "data": {"step": 2}},
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        },
    )
    wf_id = res.json()["id"]

    # Update workflow: remove n2, add n3, modify n1
    client.put(
        f"/api/v1/workflows/{wf_id}",
        json={
            "name": "Diff Test Updated",
            "nodes": [
                {"id": "n1", "name": "Start Modified", "data": {"step": 10}},
                {"id": "n3", "name": "New Step", "data": {"step": 3}},
            ],
            "edges": [{"id": "e2", "source": "n1", "target": "n3"}],
        },
    )

    # Call diff endpoint between rev 1 and rev 2
    diff_res = client.get(
        f"/api/v1/workflows/{wf_id}/revisions/diff?from_rev=1&to_rev=2"
    )
    assert diff_res.status_code == 200
    diff_data = diff_res.json()
    assert diff_data["source_revision_number"] == 1
    assert diff_data["target_revision_number"] == 2

    # Check node diffs
    assert any(n["id"] == "n3" for n in diff_data["nodes_added"])
    assert any(n["id"] == "n2" for n in diff_data["nodes_removed"])
    assert any(n["id"] == "n1" for n in diff_data["nodes_modified"])

    # Check edge diffs
    assert any(e["id"] == "e2" for e in diff_data["edges_added"])
    assert any(e["id"] == "e1" for e in diff_data["edges_removed"])


def test_verified_revision_promotion_requires_execution_evidence(client: TestClient):
    """Verify that promoting an unverified revision strictly requires passing execution evidence."""
    # 1. Create workflow (rev 1)
    res = client.post(
        "/api/v1/workflows",
        json={"name": "Promotion Test", "nodes": [{"id": "n1"}], "edges": []},
    )
    wf_id = res.json()["id"]

    # 2. Update to create rev 2 (unverified by default)
    up_res = client.put(
        f"/api/v1/workflows/{wf_id}",
        json={"name": "Promotion Test Updated", "nodes": [{"id": "n1"}, {"id": "n2"}], "edges": []},
    )
    rev2_id = up_res.json()["active_revision_id"]

    # 3. Attempt to promote rev 2 without valid execution evidence -> 412/400
    promo_fail = client.post(
        f"/api/v1/workflows/{wf_id}/revisions/{rev2_id}/promote",
        json={"execution_id": "non-existent-exec-id"},
    )
    assert promo_fail.status_code in (400, 412)

    # 4. Create a failed execution
    exec_fail_res = client.post(
        f"/api/v1/workflows/{wf_id}/executions",
        json={"status": "failed", "error_message": "Failed run"},
    )
    exec_fail_id = exec_fail_res.json()["id"]

    # Attempt to promote with failed execution -> 412/400
    promo_fail_status = client.post(
        f"/api/v1/workflows/{wf_id}/revisions/{rev2_id}/promote",
        json={"execution_id": exec_fail_id},
    )
    assert promo_fail_status.status_code in (400, 412)

    # 5. Create a successful (completed) execution
    exec_pass_res = client.post(
        f"/api/v1/workflows/{wf_id}/executions",
        json={"status": "completed", "output_data": {"test": "ok"}},
    )
    exec_pass_id = exec_pass_res.json()["id"]

    # Promote with completed execution -> 200 OK
    promo_success = client.post(
        f"/api/v1/workflows/{wf_id}/revisions/{rev2_id}/promote",
        json={"execution_id": exec_pass_id},
    )
    assert promo_success.status_code == 200
    promoted_rev = promo_success.json()
    assert promoted_rev["is_verified"] is True
    assert promoted_rev["is_active"] is True
    assert promoted_rev["last_execution_id"] == exec_pass_id


def test_revision_restoration(client: TestClient):
    """Verify that restoring a previous revision creates a new revision copying the historical snapshot."""
    # 1. Create workflow (rev 1: single node)
    res = client.post(
        "/api/v1/workflows",
        json={"name": "Restore Test", "nodes": [{"id": "n1", "name": "V1 Node"}], "edges": []},
    )
    wf_id = res.json()["id"]
    rev1_id = res.json()["active_revision_id"]

    # 2. Update to rev 2 (two nodes)
    client.put(
        f"/api/v1/workflows/{wf_id}",
        json={"name": "Restore Test V2", "nodes": [{"id": "n1"}, {"id": "n2"}], "edges": []},
    )

    # 3. Restore to rev 1
    restore_res = client.post(
        f"/api/v1/workflows/{wf_id}/revisions/{rev1_id}/restore",
        json={"change_summary": "Rollback to stable baseline"},
    )
    assert restore_res.status_code == 200
    restored_rev = restore_res.json()
    assert restored_rev["revision_number"] == 3
    # Restored revision snapshot should now only have the 1 node from rev 1
    assert len(restored_rev["snapshot"]["nodes"]) == 1
    assert restored_rev["snapshot"]["nodes"][0]["id"] == "n1"

    # Verify workflow itself was updated
    wf_res = client.get(f"/api/v1/workflows/{wf_id}")
    assert wf_res.status_code == 200
    wf_data = wf_res.json()
    assert wf_data["current_revision_number"] == 3
    assert len(wf_data["nodes"]) == 1
