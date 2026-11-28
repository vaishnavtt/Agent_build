import io
import os
import pypdf
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.engine.pricing import calculate_estimated_cost_usd
from app.engine.runner import execution_engine
from app.engine.types import ExecutionStatus
from app.engine.adapters import Member4WorkflowExecutor, Member4RepairIntegrationAdapter
from app.database.session import SessionLocal


client = TestClient(app)


def _create_minimal_pdf(content: str = "AgentForge Candidate Resume: 5 years Python and FastAPI experience.") -> bytes:
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


# =============================================================================
# 1. LIVE DOCUMENT UPLOAD PIPELINE TESTS
# =============================================================================

def test_document_upload_valid_pdf_and_retrieval():
    pdf_bytes = _create_minimal_pdf()
    file_tuple = ("candidate_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")

    resp = client.post("/api/v1/documents/upload", files={"file": file_tuple})
    assert resp.status_code == 201
    data = resp.json()

    assert data["status"] == "ready"
    assert "document_id" in data
    assert data["filename"] == "candidate_resume.pdf"
    assert os.path.exists(data["file_path"])
    doc_id = data["document_id"]

    # Verify retrieval endpoint
    get_resp = client.get(f"/api/v1/documents/{doc_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["exists"] is True


def test_document_upload_rejects_invalid_extension():
    fake_exe = ("malware.exe", io.BytesIO(b"MZBINARY"), "application/octet-stream")
    resp = client.post("/api/v1/documents/upload", files={"file": fake_exe})
    assert resp.status_code == 400
    assert "unsupported file format" in resp.json()["detail"].lower()


def test_document_upload_rejects_corrupted_pdf_header():
    fake_pdf = ("corrupt.pdf", io.BytesIO(b"NOT_A_REAL_PDF_HEADER_12345"), "application/pdf")
    resp = client.post("/api/v1/documents/upload", files={"file": fake_pdf})
    assert resp.status_code == 400
    assert "signature" in resp.json()["detail"].lower() or "header" in resp.json()["detail"].lower()


def test_document_upload_rejects_empty_file():
    empty_pdf = ("empty.pdf", io.BytesIO(b""), "application/pdf")
    resp = client.post("/api/v1/documents/upload", files={"file": empty_pdf})
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_uploaded_document_integration_with_document_reader_node():
    """Verifies that the Document Reader node can execute using the file_path returned by the upload endpoint."""
    pdf_bytes = _create_minimal_pdf()
    file_tuple = ("test_doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    upload_resp = client.post("/api/v1/documents/upload", files={"file": file_tuple})
    assert upload_resp.status_code == 201
    stored_path = upload_resp.json()["file_path"]

    workflow = {
        "id": "wf_uploaded_doc_read",
        "nodes": [
            {"id": "n_in", "type": "Input", "config": {}},
            {"id": "n_reader", "type": "Document Reader", "config": {}},
            {"id": "n_out", "type": "Output", "config": {"outputFormat": "json"}},
        ],
        "edges": [
            {"id": "e1", "source": "n_in", "target": "n_reader"},
            {"id": "e2", "source": "n_reader", "target": "n_out"},
        ],
    }

    report = await execution_engine.execute(workflow, {"n_in": {"file_path": stored_path}})
    assert report.status == ExecutionStatus.SUCCESS
    assert report.metrics.nodes_executed == 3


# =============================================================================
# 2. EXECUTION PRICING & COST METRICS TESTS
# =============================================================================

def test_cost_calculation_zero_tokens():
    assert calculate_estimated_cost_usd("gemini-1.5-pro", 0, 0) == 0.0
    assert calculate_estimated_cost_usd("gemini-1.5-flash", -10, 0) == 0.0


def test_cost_calculation_gemini_15_pro():
    # 1,000,000 prompt tokens = $1.25; 1,000,000 completion = $5.00
    cost = calculate_estimated_cost_usd("gemini-1.5-pro", 1_000_000, 1_000_000)
    assert cost == 6.25

    # 10,000 prompt tokens ($0.0125) + 2,000 completion ($0.0100) = $0.0225
    cost_small = calculate_estimated_cost_usd("gemini-1.5-pro", 10_000, 2_000)
    assert cost_small == 0.0225


def test_cost_calculation_gemini_15_flash():
    # 1.5 Flash rates: $0.075 / 1M prompt, $0.30 / 1M completion
    cost = calculate_estimated_cost_usd("gemini-1.5-flash", 1_000_000, 1_000_000)
    assert cost == 0.375


def test_cost_calculation_gemini_20_flash():
    # 2.0 Flash rates: $0.10 / 1M prompt, $0.40 / 1M completion
    cost = calculate_estimated_cost_usd("gemini-2.0-flash", 1_000_000, 1_000_000)
    assert cost == 0.50


def test_cost_calculation_fallback_unknown_model():
    cost = calculate_estimated_cost_usd("unknown-experimental-model", 1_000_000, 0)
    # Falls back to gemini-1.5-pro rates safely ($1.25)
    assert cost == 1.25


@pytest.mark.asyncio
async def test_llm_execution_metrics_include_estimated_cost():
    workflow = {
        "id": "wf_cost_metrics",
        "nodes": [
            {"id": "n_in", "type": "Input", "config": {}},
            {"id": "n_llm", "type": "LLM", "config": {"apiKey": "mock-key", "model": "gemini-1.5-pro"}},
            {"id": "n_out", "type": "Output", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n_in", "target": "n_llm"},
            {"id": "e2", "source": "n_llm", "target": "n_out"},
        ],
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Evaluated successfully."}]}}],
        "usageMetadata": {
            "promptTokenCount": 200_000,     # 200k * $1.25/M = $0.25
            "candidatesTokenCount": 50_000,  # 50k * $5.00/M = $0.25 -> Total $0.50
            "totalTokenCount": 250_000,
        },
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        report = await execution_engine.execute(workflow, {"n_in": "Candidate payload"})

    assert report.status == ExecutionStatus.SUCCESS
    assert report.metrics.estimated_cost_usd is not None
    assert report.metrics.estimated_cost_usd == 0.50


# =============================================================================
# 3. MEMBER 3 CANONICAL WORKFLOW SCENARIOS
# =============================================================================

@pytest.mark.asyncio
async def test_member3_scenario_1_simple_linear():
    """Scenario 1: Input -> Output."""
    wf = {
        "id": "m3_sc1",
        "nodes": [
            {"id": "in", "type": "Input", "config": {"defaultValue": "Standard Query"}},
            {"id": "out", "type": "Output", "config": {"outputFormat": "json"}},
        ],
        "edges": [{"id": "e1", "source": "in", "target": "out"}],
    }
    report = await execution_engine.execute(wf, {})
    assert report.status == ExecutionStatus.SUCCESS
    assert report.result["result"] == "Standard Query"


@pytest.mark.asyncio
async def test_member3_scenario_2_conditional_branching():
    """Scenario 2: Input -> Condition -> [True: LLM, False: Tool] -> Output."""
    wf = {
        "id": "m3_sc2",
        "nodes": [
            {"id": "in", "type": "Input", "config": {}},
            {"id": "cond", "type": "Condition", "config": {"operator": "==", "value": "ai"}},
            {"id": "llm", "type": "LLM", "config": {"apiKey": "mock", "prompt": "Process AI"}},
            {"id": "tool", "type": "Tool", "config": {"toolName": "text_formatter", "operation": "upper"}},
            {"id": "out", "type": "Output", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "in", "target": "cond"},
            {"id": "e_true", "source": "cond", "target": "llm", "sourceHandle": "true"},
            {"id": "e_false", "source": "cond", "target": "tool", "sourceHandle": "false"},
            {"id": "e_llm_out", "source": "llm", "target": "out"},
            {"id": "e_tool_out", "source": "tool", "target": "out"},
        ],
    }

    # Test False branch -> Tool executes, LLM skipped, Output executes
    report = await execution_engine.execute(wf, {"in": "calc"})
    assert report.status == ExecutionStatus.SUCCESS
    statuses = {log.node_id: log.status for log in report.node_logs}
    assert statuses["tool"] == ExecutionStatus.SUCCESS
    assert statuses["llm"] == ExecutionStatus.SKIPPED
    assert statuses["out"] == ExecutionStatus.SUCCESS


@pytest.mark.asyncio
async def test_member3_scenario_3_branch_joins():
    """Scenario 3: Input -> Condition -> [Tool A / Tool B] -> Converged Join at Formatter -> Output."""
    wf = {
        "id": "m3_sc3",
        "nodes": [
            {"id": "in", "type": "Input", "config": {}},
            {"id": "cond", "type": "Condition", "config": {"operator": ">=", "value": 50}},
            {"id": "tool_high", "type": "Tool", "config": {"toolName": "text_formatter", "operation": "upper"}},
            {"id": "tool_low", "type": "Tool", "config": {"toolName": "text_formatter", "operation": "lower"}},
            {"id": "join_tool", "type": "Tool", "config": {"toolName": "text_formatter", "operation": "strip"}},
            {"id": "out", "type": "Output", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "in", "target": "cond"},
            {"id": "e_t", "source": "cond", "target": "tool_high", "sourceHandle": "true"},
            {"id": "e_f", "source": "cond", "target": "tool_low", "sourceHandle": "false"},
            {"id": "e_j1", "source": "tool_high", "target": "join_tool"},
            {"id": "e_j2", "source": "tool_low", "target": "join_tool"},
            {"id": "e_out", "source": "join_tool", "target": "out"},
        ],
    }

    report = await execution_engine.execute(wf, {"in": 75})
    assert report.status == ExecutionStatus.SUCCESS
    statuses = {log.node_id: log.status for log in report.node_logs}
    assert statuses["tool_high"] == ExecutionStatus.SUCCESS
    assert statuses["tool_low"] == ExecutionStatus.SKIPPED
    assert statuses["join_tool"] == ExecutionStatus.SUCCESS


@pytest.mark.asyncio
async def test_member3_scenario_4_human_approval_pause_and_resume():
    """Scenario 4: Input -> Document Reader -> Human Approval -> Output."""
    pdf_bytes = _create_minimal_pdf()
    wf = {
        "id": "m3_sc4",
        "nodes": [
            {"id": "in", "type": "Input", "config": {}},
            {"id": "reader", "type": "Document Reader", "config": {}},
            {"id": "gate", "type": "Human Approval", "config": {"prompt": "Confirm hiring manager sign-off"}},
            {"id": "out", "type": "Output", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "in", "target": "reader"},
            {"id": "e2", "source": "reader", "target": "gate"},
            {"id": "e3", "source": "gate", "target": "out"},
        ],
    }

    report = await execution_engine.execute(wf, {"in": pdf_bytes})
    assert report.status == ExecutionStatus.WAITING_FOR_APPROVAL
    assert report.waiting_node_id == "gate"


@pytest.mark.asyncio
async def test_member3_scenario_5_tool_chain_pipeline():
    """Scenario 5: Multi-tool pipeline (Calculator AST -> Formatter -> JSON parser)."""
    wf = {
        "id": "m3_sc5",
        "nodes": [
            {"id": "in", "type": "Input", "config": {}},
            {"id": "calc", "type": "Tool", "config": {"toolName": "calculator"}},
            {"id": "fmt", "type": "Tool", "config": {"toolName": "text_formatter", "operation": "upper"}},
            {"id": "out", "type": "Output", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "in", "target": "calc"},
            {"id": "e2", "source": "calc", "target": "fmt"},
            {"id": "e3", "source": "fmt", "target": "out"},
        ],
    }

    report = await execution_engine.execute(wf, {"in": {"expression": "(10 + 15) * 4"}})
    assert report.status == ExecutionStatus.SUCCESS
    assert "100" in str(report.result)


# =============================================================================
# 4. MEMBER 5 RELIABILITY LAB ADAPTER INTERFACE CONTRACT
# =============================================================================

@pytest.mark.asyncio
async def test_member5_adapter_execution_result_contract():
    adapter = Member4WorkflowExecutor(db_session_factory=SessionLocal)
    sample_wf = {
        "id": "wf_m5_contract",
        "nodes": [
            {"id": "i", "type": "Input", "config": {}},
            {"id": "o", "type": "Output", "config": {}},
        ],
        "edges": [{"id": "e1", "source": "i", "target": "o"}],
    }

    res = await adapter.execute("wf_m5_contract", {"i": "payload"}, workflow_override=sample_wf)

    # Verifies all 5 fields required by Member 5's ExecutionResult Pydantic schema
    assert "status" in res
    assert res["status"] in ("COMPLETED", "FAILED", "TIMEOUT", "SAFE_REJECTION")
    assert "output_data" in res
    assert "execution_trace" in res
    assert "error" in res
    assert "duration_ms" in res
    assert isinstance(res["execution_trace"], list)
    assert res["status"] == "COMPLETED"


# =============================================================================
# 5. MEMBER 6 REPAIR INTEGRATION ADAPTER CONTRACT
# =============================================================================

def test_member6_failure_information_contract():
    fail_payload = {
        "workflow": {
            "id": "wf_m6_evidence",
            "nodes": [
                {"id": "in1", "type": "Input", "config": {}},
                {"id": "calc1", "type": "Tool", "config": {"toolName": "calculator"}},
                {"id": "out1", "type": "Output", "config": {}},
            ],
            "edges": [
                {"id": "e1", "source": "in1", "target": "calc1"},
                {"id": "e2", "source": "calc1", "target": "out1"},
            ],
        },
        "inputs": {"in1": {"expression": "100 / 0"}},
    }
    resp = client.post("/api/v1/executions/run", json=fail_payload)
    exec_id = resp.json()["execution_id"]

    db = SessionLocal()
    try:
        evidence = Member4RepairIntegrationAdapter.get_failure_evidence(
            db=db,
            workflow_id="wf_m6_evidence",
            workflow_revision_id="",
            execution_run_id=exec_id,
        )
        assert evidence is not None
        # Verify required FailureInformation fields
        assert evidence["workflow_id"] == "wf_m6_evidence"
        assert evidence["execution_run_id"] == exec_id
        assert evidence["status"] == "FAILED"
        assert evidence["failed_node_id"] == "calc1"
        assert "division by zero" in evidence["error_message"].lower()

        # Verify required DiagnosisContext fields
        assert "nodes" in evidence
        assert "edges" in evidence
        assert len(evidence["nodes"]) == 3
        assert len(evidence["edges"]) == 2
    finally:
        db.close()
