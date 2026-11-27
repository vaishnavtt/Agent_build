import io
import os
import pypdf
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.engine.runner import execution_engine
from app.engine.security import validate_outbound_url, validate_document_path, redact_sensitive_data
from app.engine.types import (
    ExecutionContext,
    ExecutionStatus,
    ToolExecutionError,
    NodeExecutionError,
    WorkflowValidationError,
)
from app.engine.adapters import Member4WorkflowExecutor, Member4RepairIntegrationAdapter
from app.database.session import SessionLocal
from app.services.execution_service import ExecutionService


def _create_sample_pdf(text: str = "Quarterly Business Review: Sales up 35 percent.") -> bytes:
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


# -----------------------------------------------------------------------------
# 1. Diamond conditional branching join test
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_diamond_conditional_branch_join():
    """Verifies that when Condition takes one branch, the unchosen branch is skipped
    but the join node (reachable by the taken branch) executes successfully."""
    workflow = {
        "id": "wf_diamond_join",
        "nodes": [
            {"id": "n_in", "type": "Input", "name": "Input Step", "config": {}},
            {
                "id": "n_cond",
                "type": "Condition",
                "name": "Branch Condition",
                "config": {"operator": "==", "value": "vip"},
            },
            {
                "id": "n_vip",
                "type": "Tool",
                "name": "VIP Formatter",
                "config": {"toolName": "text_formatter", "operation": "upper"},
            },
            {
                "id": "n_standard",
                "type": "Tool",
                "name": "Standard Formatter",
                "config": {"toolName": "text_formatter", "operation": "lower"},
            },
            {
                "id": "n_join",
                "type": "Output",
                "name": "Converged Output",
                "config": {"outputFormat": "json"},
            },
        ],
        "edges": [
            {"id": "e1", "source": "n_in", "target": "n_cond"},
            {"id": "e_true", "source": "n_cond", "target": "n_vip", "sourceHandle": "true"},
            {"id": "e_false", "source": "n_cond", "target": "n_standard", "sourceHandle": "false"},
            {"id": "e_join1", "source": "n_vip", "target": "n_join"},
            {"id": "e_join2", "source": "n_standard", "target": "n_join"},
        ],
    }

    # True branch taken: n_vip runs, n_standard skipped, n_join executes
    report_vip = await execution_engine.execute(workflow, {"n_in": "vip"})
    assert report_vip.status == ExecutionStatus.SUCCESS
    states_vip = {log.node_id: log.status for log in report_vip.node_logs}
    assert states_vip["n_vip"] == ExecutionStatus.SUCCESS
    assert states_vip["n_standard"] == ExecutionStatus.SKIPPED
    assert states_vip["n_join"] == ExecutionStatus.SUCCESS

    # False branch taken: n_standard runs, n_vip skipped, n_join executes
    report_std = await execution_engine.execute(workflow, {"n_in": "regular"})
    assert report_std.status == ExecutionStatus.SUCCESS
    states_std = {log.node_id: log.status for log in report_std.node_logs}
    assert states_std["n_vip"] == ExecutionStatus.SKIPPED
    assert states_std["n_standard"] == ExecutionStatus.SUCCESS
    assert states_std["n_join"] == ExecutionStatus.SUCCESS


# -----------------------------------------------------------------------------
# 2. SSRF Protection: blocked loopback and private IP targets
# -----------------------------------------------------------------------------
def test_ssrf_blocking_loopback_and_metadata():
    with pytest.raises(ToolExecutionError) as exc1:
        validate_outbound_url("http://127.0.0.1:8000/api/internal")
    assert "blocked" in str(exc1.value).lower()

    with pytest.raises(ToolExecutionError) as exc2:
        validate_outbound_url("http://localhost:5000/metrics")
    assert "blocked" in str(exc2.value).lower()

    with pytest.raises(ToolExecutionError) as exc3:
        validate_outbound_url("http://169.254.169.254/latest/meta-data/")
    assert "blocked" in str(exc3.value).lower()


# -----------------------------------------------------------------------------
# 3. Path Traversal & Unsafe Document Directory Blocking
# -----------------------------------------------------------------------------
def test_document_path_traversal_blocking():
    with pytest.raises(NodeExecutionError) as exc1:
        validate_document_path("../../etc/passwd", node_id="doc1")
    assert "traversal" in str(exc1.value).lower() or "denied" in str(exc1.value).lower()

    with pytest.raises(NodeExecutionError) as exc2:
        validate_document_path("C:\\Windows\\System32\\drivers\\etc\\hosts", node_id="doc1")
    assert "access denied" in str(exc2.value).lower() or "outside" in str(exc2.value).lower()


# -----------------------------------------------------------------------------
# 4. Sensitive Data Redaction
# -----------------------------------------------------------------------------
def test_sensitive_data_redaction():
    payload = {
        "gemini_api_key": "AIzaSySecretToken12345",
        "nested": {
            "password": "SuperSecretPassword!",
            "public_metric": 42,
        },
        "url": "https://api.example.com/v1?token=xyz987&other=safe",
    }
    redacted = redact_sensitive_data(payload)
    assert redacted["gemini_api_key"] == "[REDACTED]"
    assert redacted["nested"]["password"] == "[REDACTED]"
    assert redacted["nested"]["public_metric"] == 42
    assert "xyz987" not in str(redacted["url"])


# -----------------------------------------------------------------------------
# 5. Ad Hoc Workflow Approval and Atomic Claim API Test
# -----------------------------------------------------------------------------
def test_ad_hoc_workflow_approval_and_duplicate_prevention():
    client = TestClient(app)

    ad_hoc_approval_wf = {
        "workflow": {
            "id": "adhoc_gate_wf",
            "name": "AdHoc Approval Test",
            "nodes": [
                {"id": "n1", "type": "Input", "name": "Start", "config": {}},
                {"id": "n2", "type": "Human Approval", "name": "Manager Gate", "config": {}},
                {"id": "n3", "type": "Output", "name": "Finish", "config": {}},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ],
        },
        "inputs": {"n1": "Ad hoc invoice review"},
    }

    # 1. Run directly via /executions/run
    run_resp = client.post("/api/v1/executions/run", json=ad_hoc_approval_wf)
    assert run_resp.status_code == 200
    report = run_resp.json()
    assert report["status"] == "WAITING_FOR_APPROVAL"
    assert report["waiting_node_id"] == "n2"
    exec_id = report["execution_id"]

    # 2. Approve via /executions/{id}/approve
    approve_resp = client.post(
        f"/api/v1/executions/{exec_id}/approve",
        json={"comment": "Approved by Ad Hoc Auditor"},
    )
    assert approve_resp.status_code == 200
    resumed_report = approve_resp.json()
    assert resumed_report["status"] == "SUCCESS"

    # 3. Duplicate approval attempt on same execution must return HTTP 409 Conflict
    dup_resp = client.post(
        f"/api/v1/executions/{exec_id}/approve",
        json={"comment": "Duplicate approval attempt"},
    )
    assert dup_resp.status_code == 409


# -----------------------------------------------------------------------------
# 6. Execution Cancellation API Test
# -----------------------------------------------------------------------------
def test_execution_cancellation_flow():
    client = TestClient(app)

    wf_payload = {
        "workflow": {
            "id": "cancel_wf",
            "name": "Cancellation Workflow",
            "nodes": [
                {"id": "n1", "type": "Input", "name": "Start", "config": {}},
                {"id": "n2", "type": "Human Approval", "name": "Gate", "config": {}},
                {"id": "n3", "type": "Output", "name": "Finish", "config": {}},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ],
        },
        "inputs": {"n1": "Pending approval to be cancelled"},
    }

    run_resp = client.post("/api/v1/executions/run", json=wf_payload)
    exec_id = run_resp.json()["execution_id"]

    cancel_resp = client.post(f"/api/v1/executions/{exec_id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"

    # Verify execution record status
    get_resp = client.get(f"/api/v1/executions/{exec_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "CANCELLED"


# -----------------------------------------------------------------------------
# 7. Member 5 Reliability Lab Adapter Contract Test
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_member5_workflow_executor_adapter():
    adapter = Member4WorkflowExecutor(db_session_factory=SessionLocal)
    workflow_override = {
        "id": "m5_test_wf",
        "nodes": [
            {"id": "in1", "type": "Input", "name": "Input", "config": {}},
            {"id": "out1", "type": "Output", "name": "Output", "config": {}},
        ],
        "edges": [{"id": "e1", "source": "in1", "target": "out1"}],
    }

    result = await adapter.execute(
        workflow_id="m5_test_wf",
        input_payload={"in1": "reliability scenario payload"},
        workflow_override=workflow_override,
    )

    assert result["status"] == "COMPLETED"
    assert result["output_data"] is not None
    assert len(result["execution_trace"]) == 2
    assert result["duration_ms"] >= 0.0


# -----------------------------------------------------------------------------
# 8. Member 6 Self-Repair Adapter Contract Test
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_member6_repair_integration_adapter():
    client = TestClient(app)

    # Trigger a failed execution
    fail_payload = {
        "workflow": {
            "id": "wf_repair_m6",
            "name": "Repair Target",
            "nodes": [
                {"id": "n1", "type": "Input", "name": "Input", "config": {}},
                {"id": "n2", "type": "Tool", "name": "Divide Calc", "config": {"toolName": "calculator"}},
                {"id": "n3", "type": "Output", "name": "Output", "config": {}},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ],
        },
        "inputs": {"n1": {"expression": "50 / 0"}},
    }
    resp = client.post("/api/v1/executions/run", json=fail_payload)
    exec_id = resp.json()["execution_id"]

    db = SessionLocal()
    try:
        evidence = Member4RepairIntegrationAdapter.get_failure_evidence(
            db=db,
            workflow_id="wf_repair_m6",
            workflow_revision_id="",
            execution_run_id=exec_id,
        )
        assert evidence is not None
        assert evidence["status"] == "FAILED"
        assert evidence["failed_node_id"] == "n2"
        assert "division by zero" in evidence["error_message"].lower()

        # Test isolated candidate execution of repaired graph
        repaired_wf = {
            "id": "wf_repair_m6",
            "name": "Repair Target",
            "nodes": [
                {"id": "n1", "type": "Input", "name": "Input", "config": {}},
                {"id": "n2", "type": "Tool", "name": "Divide Calc", "config": {"toolName": "calculator"}},
                {"id": "n3", "type": "Output", "name": "Output", "config": {}},
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
            ],
        }
        candidate_report = await Member4RepairIntegrationAdapter.execute_isolated_candidate(
            candidate_workflow=repaired_wf,
            inputs={"n1": {"expression": "50 / 2"}},
        )
        assert candidate_report.status == ExecutionStatus.SUCCESS
        assert candidate_report.result["result"]["result"] == 25.0
    finally:
        db.close()


# -----------------------------------------------------------------------------
# 9. Isolated Candidate Execution Side-Effect Blocking
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_isolated_candidate_blocks_mutating_http():
    candidate_wf = {
        "id": "wf_candidate_http",
        "nodes": [
            {"id": "n1", "type": "Input", "config": {}},
            {
                "id": "n2",
                "type": "Tool",
                "config": {"toolName": "http_request", "method": "POST", "url": "https://httpbin.org/post"},
            },
            {"id": "n3", "type": "Output", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
        ],
    }

    report = await execution_engine.execute(
        candidate_wf,
        {"n1": {}},
        candidate_mode=True,
    )
    assert report.status == ExecutionStatus.FAILED
    assert "blocked during isolated candidate execution" in str(report.error_message).lower()


# -----------------------------------------------------------------------------
# 10. Member 3 Generated Workflow Format Compatibility
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_member3_generated_workflow_compatibility():
    """Validates compatibility with Member 3 React Flow style node shapes (data.componentType, etc)."""
    m3_workflow = {
        "id": "m3_generated_agent",
        "name": "Customer Feedback Categorizer",
        "version": "1.0.0",
        "nodes": [
            {
                "id": "node_input",
                "type": "customWorkflow",
                "position": {"x": 50, "y": 100},
                "data": {
                    "label": "Incoming Review",
                    "componentType": "Input",
                    "config": {"inputType": "text", "required": True},
                },
            },
            {
                "id": "node_formatter",
                "type": "customWorkflow",
                "position": {"x": 250, "y": 100},
                "data": {
                    "label": "Text Sanitizer",
                    "componentType": "Tool",
                    "config": {"toolName": "text_formatter", "operation": "strip"},
                },
            },
            {
                "id": "node_finish",
                "type": "customWorkflow",
                "position": {"x": 450, "y": 100},
                "data": {
                    "label": "Final Output",
                    "componentType": "Output",
                    "config": {"outputFormat": "json"},
                },
            },
        ],
        "edges": [
            {"id": "e1", "source": "node_input", "target": "node_formatter"},
            {"id": "e2", "source": "node_formatter", "target": "node_finish"},
        ],
    }

    report = await execution_engine.execute(
        m3_workflow,
        {"node_input": "  AgentForge works smoothly!  "},
    )
    assert report.status == ExecutionStatus.SUCCESS
    assert report.metrics.nodes_executed == 3
    assert report.result["result"]["result"] == "AgentForge works smoothly!"
