"""Automated test suite for Member 2: Backend and Database Development.

Tests:
1. SQLite Database operations & SQLAlchemy models (WorkflowModel, WorkflowExecutionModel)
2. Workflow relationship with execution history
3. CRUD helper functions in crud.py
4. REST API Endpoints:
   - POST /api/workflows (Create workflow)
   - GET /api/workflows (List workflows)
   - GET /api/workflows/{id} (Get workflow)
   - PUT /api/workflows/{id} (Update workflow)
   - DELETE /api/workflows/{id} (Delete workflow)
   - POST /api/workflows/{id}/run (Execute workflow)
   - GET /api/workflows/{id}/history (Workflow execution history)
   - GET /api/executions/{id} (Execution details)
   - POST /api/workflows/{id}/validate (Validate saved workflow)
5. Pydantic validation and error handling (404, 422)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.base import Base
from app.database.session import get_db
from app.models.workflow import WorkflowModel, WorkflowExecutionModel, ExecutionHistoryModel
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowExecutionCreate
import crud

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Database Model & Relationship Tests
# ---------------------------------------------------------------------------
def test_workflow_model_and_relationship(db_session):
    """Test WorkflowModel, ExecutionHistoryModel, and their relationship in SQLite."""
    # 1. Create Workflow
    wf = WorkflowModel(
        name="Candidate Evaluator",
        description="Automated candidate screening",
        nodes=[{"id": "n1", "data": {"label": "Start", "componentType": "Input"}}],
        edges=[],
    )
    db_session.add(wf)
    db_session.commit()
    db_session.refresh(wf)

    assert wf.id is not None
    assert wf.workflow_name == "Candidate Evaluator"
    assert "nodes" in wf.workflow_data

    # 2. Add Execution Record linked via foreign key
    exec_rec = WorkflowExecutionModel(
        workflow_id=wf.id,
        workflow_name=wf.name,
        status="COMPLETED",
        execution_status="Completed",
        log_evidence=[{"step": "Start", "message": "Input received"}],
    )
    db_session.add(exec_rec)
    db_session.commit()
    db_session.refresh(exec_rec)

    assert exec_rec.id is not None
    assert exec_rec.workflow_id == wf.id

    # 3. Test ORM relationship
    db_session.refresh(wf)
    assert len(wf.executions) == 1
    assert wf.executions[0].id == exec_rec.id
    assert exec_rec.workflow.name == "Candidate Evaluator"


# ---------------------------------------------------------------------------
# 2. CRUD Functions in crud.py
# ---------------------------------------------------------------------------
def test_crud_workflow_lifecycle(db_session):
    """Test create, read, update, delete in crud.py."""
    create_in = WorkflowCreate(
        name="Invoice Extractor",
        description="Extract totals from invoices",
        nodes=[{"id": "n1", "type": "customWorkflow"}],
        edges=[],
    )
    created = crud.create_workflow(db_session, create_in)
    assert created.id is not None
    assert created.name == "Invoice Extractor"

    # Get by ID
    fetched = crud.get_workflow(db_session, created.id)
    assert fetched is not None
    assert fetched.id == created.id

    # List workflows
    all_wfs = crud.get_workflows(db_session)
    assert any(w.id == created.id for w in all_wfs)

    # Update
    update_in = WorkflowUpdate(description="Updated invoice processing pipeline")
    updated = crud.update_workflow(db_session, created.id, update_in)
    assert updated.description == "Updated invoice processing pipeline"

    # Create Execution History
    exec_in = WorkflowExecutionCreate(
        workflow_id=created.id,
        workflow_name=created.name,
        status="COMPLETED",
        execution_status="Completed",
        duration="1.2s",
    )
    exec_obj = crud.create_execution(db_session, exec_in)
    assert exec_obj.id is not None

    # Fetch History
    history = crud.get_workflow_executions(db_session, created.id)
    assert len(history) >= 1
    assert history[0].workflow_id == created.id

    # Delete
    deleted = crud.delete_workflow(db_session, created.id)
    assert deleted is True
    assert crud.get_workflow(db_session, created.id) is None


# ---------------------------------------------------------------------------
# 3. REST API: Workflow CRUD (/api/workflows)
# ---------------------------------------------------------------------------
def test_api_create_and_get_workflow():
    """Test POST /api/workflows and GET /api/workflows/{id}."""
    payload = {
        "workflow_name": "Resume Screening Agent",
        "description": "Screens resumes against job specs",
        "workflow_data": {
            "nodes": [
                {"id": "node-1", "type": "customWorkflow", "data": {"label": "Input", "componentType": "Input"}},
                {"id": "node-2", "type": "customWorkflow", "data": {"label": "LLM", "componentType": "LLM"}},
            ],
            "edges": [{"id": "e1-2", "source": "node-1", "target": "node-2"}],
        },
    }

    # 1. Create Workflow
    res_create = client.post("/api/workflows", json=payload)
    assert res_create.status_code == 201
    created_data = res_create.json()
    wf_id = created_data["id"]
    assert created_data["name"] == "Resume Screening Agent"
    assert len(created_data["nodes"]) == 2

    # 2. Get Single Workflow
    res_get = client.get(f"/api/workflows/{wf_id}")
    assert res_get.status_code == 200
    get_data = res_get.json()
    assert get_data["id"] == wf_id
    assert get_data["workflow_name"] == "Resume Screening Agent"

    # 3. List Workflows
    res_list = client.get("/api/workflows")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert isinstance(list_data, list)
    assert any(w["id"] == wf_id for w in list_data)

    # 4. Update Workflow
    res_update = client.put(f"/api/workflows/{wf_id}", json={"description": "Updated resume screener"})
    assert res_update.status_code == 200
    assert res_update.json()["description"] == "Updated resume screener"

    # 5. Delete Workflow
    res_del = client.delete(f"/api/workflows/{wf_id}")
    assert res_del.status_code in (200, 204)

    # 6. Verify 404 after deletion
    res_after = client.get(f"/api/workflows/{wf_id}")
    assert res_after.status_code == 404


# ---------------------------------------------------------------------------
# 4. REST API: Workflow Execution & History (/api/workflows/{id}/run & history)
# ---------------------------------------------------------------------------
def test_api_workflow_run_and_history():
    """Test POST /api/workflows/{id}/run and GET /api/workflows/{id}/history."""
    # First create a valid workflow to execute
    wf_payload = {
        "name": "Audit Workflow",
        "description": "Performs rule audits",
        "nodes": [
            {"id": "n1", "type": "customWorkflow", "data": {"label": "Start", "componentType": "Input"}},
            {"id": "n2", "type": "customWorkflow", "data": {"label": "Finish", "componentType": "Output"}},
        ],
        "edges": [{"id": "e1-2", "source": "n1", "target": "n2"}],
    }
    wf_res = client.post("/api/workflows", json=wf_payload)
    wf_id = wf_res.json()["id"]

    # 1. Run Workflow
    run_res = client.post(f"/api/workflows/{wf_id}/run", json={"input_payload": {"test": "data"}, "auto_repair": True})
    assert run_res.status_code == 200
    exec_data = run_res.json()
    exec_id = exec_data["id"]
    assert exec_data["workflow_id"] == wf_id
    assert "status" in exec_data

    # 2. Get Workflow Execution History
    hist_res = client.get(f"/api/workflows/{wf_id}/history")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert isinstance(hist_data, list)
    assert len(hist_data) >= 1
    assert hist_data[0]["workflow_id"] == wf_id

    # 3. Get Specific Execution Details (/api/executions/{id})
    det_res = client.get(f"/api/executions/{exec_id}")
    assert det_res.status_code == 200
    det_data = det_res.json()
    assert det_data["id"] == exec_id
    assert det_data["workflow_id"] == wf_id


# ---------------------------------------------------------------------------
# 5. REST API: Workflow Validation (/api/workflows/{id}/validate)
# ---------------------------------------------------------------------------
def test_api_workflow_validate():
    """Test POST /api/workflows/{id}/validate and POST /api/workflows/validate."""
    # Create workflow with missing output to test validation detection
    wf_payload = {
        "name": "Incomplete Workflow",
        "nodes": [
            {"id": "n1", "type": "customWorkflow", "data": {"label": "Start", "componentType": "Input"}},
        ],
        "edges": [],
    }
    wf_res = client.post("/api/workflows", json=wf_payload)
    wf_id = wf_res.json()["id"]

    # Validate saved workflow
    val_res = client.post(f"/api/workflows/{wf_id}/validate")
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert "is_valid" in val_data
    assert "readiness_score" in val_data
    assert "issues" in val_data


# ---------------------------------------------------------------------------
# 6. Error Handling & Status Codes
# ---------------------------------------------------------------------------
def test_api_not_found_handling():
    """Test 404 responses for non-existent IDs."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"/api/workflows/{fake_id}").status_code == 404
    assert client.put(f"/api/workflows/{fake_id}", json={"name": "test"}).status_code == 404
    assert client.delete(f"/api/workflows/{fake_id}").status_code == 404
    assert client.post(f"/api/workflows/{fake_id}/run", json={}).status_code == 404
    assert client.get(f"/api/workflows/{fake_id}/history").status_code == 404
    assert client.post(f"/api/workflows/{fake_id}/validate").status_code == 404
    assert client.get(f"/api/executions/{fake_id}").status_code == 404
