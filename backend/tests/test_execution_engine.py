import io
import pytest
import pypdf
from unittest.mock import patch, MagicMock
from app.engine.runner import execution_engine
from app.engine.types import (
    WorkflowValidationError,
    CycleDetectedError,
    MissingInputError,
    UnsupportedNodeTypeError,
    GeminiConfigError,
    ToolExecutionError,
    ExecutionContext,
)
from app.schemas.execution import ExecutionStatus


def _create_sample_pdf(text: str = "AgentForge Financial Report: Q3 revenue grew by 24 percent.") -> bytes:
    """Helper creating an in-memory PDF document."""
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


# -------------------------------------------------------------------------
# 1. Simple Input -> Output workflow
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_simple_input_output_workflow():
    workflow = {
        "id": "wf_input_output",
        "nodes": [
            {"id": "node_1", "type": "Input", "name": "User Input", "config": {}},
            {"id": "node_2", "type": "Output", "name": "Result Output", "config": {"outputFormat": "json"}},
        ],
        "edges": [{"id": "e1", "source": "node_1", "target": "node_2"}],
    }
    inputs = {"node_1": "Hello AgentForge"}
    report = await execution_engine.execute(workflow, inputs)

    assert report.status == ExecutionStatus.SUCCESS
    assert report.result["result"] == "Hello AgentForge"
    assert len(report.node_logs) == 2
    assert report.metrics.nodes_executed == 2


# -------------------------------------------------------------------------
# 2. Input -> LLM -> Output workflow (Mocked Gemini API)
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_input_llm_output_workflow_with_mocked_gemini():
    workflow = {
        "id": "wf_llm",
        "nodes": [
            {"id": "n_in", "type": "Input", "name": "Prompt Input", "config": {}},
            {
                "id": "n_llm",
                "type": "LLM",
                "name": "Gemini Summarizer",
                "config": {"apiKey": "fake-gemini-key", "model": "gemini-1.5-pro", "prompt": "Summarize text"},
            },
            {"id": "n_out", "type": "Output", "name": "Final Summary", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n_in", "target": "n_llm"},
            {"id": "e2", "source": "n_llm", "target": "n_out"},
        ],
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Summary: Key metrics improved."}]}}],
        "usageMetadata": {"promptTokenCount": 35, "candidatesTokenCount": 12, "totalTokenCount": 47},
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        report = await execution_engine.execute(workflow, {"n_in": "Detailed company report text."})

    assert report.status == ExecutionStatus.SUCCESS
    assert "Summary: Key metrics improved." in str(report.result)
    assert report.metrics.total_api_calls == 1
    assert report.metrics.total_token_usage is not None
    assert report.metrics.total_token_usage.total_tokens == 47


# -------------------------------------------------------------------------
# 3. Input -> PDF Reader -> Output workflow
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_pdf_reader_workflow():
    pdf_bytes = _create_sample_pdf()
    workflow = {
        "id": "wf_pdf",
        "nodes": [
            {"id": "n_in", "type": "Input", "name": "PDF File Input", "config": {}},
            {"id": "n_pdf", "type": "Document Reader", "name": "PDF Parser", "config": {"chunkSize": 500}},
            {"id": "n_out", "type": "Output", "name": "Output Text", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n_in", "target": "n_pdf"},
            {"id": "e2", "source": "n_pdf", "target": "n_out"},
        ],
    }

    report = await execution_engine.execute(workflow, {"n_in": pdf_bytes})
    assert report.status == ExecutionStatus.SUCCESS
    assert report.metrics.nodes_executed == 3


# -------------------------------------------------------------------------
# 3b. Input -> Document Reader -> LLM -> Output workflow
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_input_document_reader_llm_output_pipeline():
    pdf_bytes = _create_sample_pdf("Annual Financial Statement: Total Net Profit increased by 42%.")
    workflow = {
        "id": "wf_doc_llm_pipeline",
        "nodes": [
            {"id": "n1", "type": "Input", "name": "PDF Input", "config": {}},
            {"id": "n2", "type": "Document Reader", "name": "Document Parser", "config": {}},
            {"id": "n3", "type": "LLM", "name": "AI Summarizer", "config": {"apiKey": "mock-key", "prompt": "Extract key highlights"}},
            {"id": "n4", "type": "Output", "name": "Final Summary", "config": {"outputFormat": "markdown"}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n3", "target": "n4"},
        ],
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Key Highlight: Net Profit grew 42%."}]}}],
        "usageMetadata": {"promptTokenCount": 80, "candidatesTokenCount": 20, "totalTokenCount": 100},
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        report = await execution_engine.execute(workflow, {"n1": pdf_bytes})

    assert report.status == ExecutionStatus.SUCCESS
    assert report.metrics.nodes_executed == 4
    assert "Net Profit grew 42%" in str(report.result)
    assert report.metrics.total_api_calls == 1
    assert report.metrics.total_token_usage.total_tokens == 100


# -------------------------------------------------------------------------
# 4. Predefined Tool execution (Calculator, Text Formatter, Web Search)
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_predefined_tool_execution():
    workflow = {
        "id": "wf_calc",
        "nodes": [
            {"id": "n1", "type": "Input", "name": "Math Input", "config": {}},
            {
                "id": "n2",
                "type": "Tool",
                "name": "Safe Calculator",
                "config": {"toolName": "calculator"},
            },
            {"id": "n3", "type": "Output", "name": "Math Output", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
        ],
    }

    report = await execution_engine.execute(workflow, {"n1": {"expression": "(12 + 8) * 5 / 2"}})
    assert report.status == ExecutionStatus.SUCCESS
    assert report.result["result"]["result"] == 50.0


# -------------------------------------------------------------------------
# 5. Condition TRUE branch execution
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_condition_true_branch():
    workflow = {
        "id": "wf_cond_true",
        "nodes": [
            {"id": "n_in", "type": "Input", "name": "Score Input", "config": {}},
            {
                "id": "n_cond",
                "type": "Condition",
                "name": "Check Threshold",
                "config": {"operator": ">=", "value": 80},
            },
            {"id": "n_true", "type": "Output", "name": "Pass Node", "config": {}},
            {"id": "n_false", "type": "Output", "name": "Fail Node", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n_in", "target": "n_cond"},
            {"id": "e_true", "source": "n_cond", "target": "n_true", "sourceHandle": "true"},
            {"id": "e_false", "source": "n_cond", "target": "n_false", "sourceHandle": "false"},
        ],
    }

    report = await execution_engine.execute(workflow, {"n_in": 95})
    assert report.status == ExecutionStatus.SUCCESS
    # n_true executed, n_false skipped
    logs_by_id = {l.node_id: l.status for l in report.node_logs}
    assert logs_by_id["n_true"] == ExecutionStatus.SUCCESS
    assert logs_by_id["n_false"] == ExecutionStatus.SKIPPED


# -------------------------------------------------------------------------
# 6. Condition FALSE branch execution
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_condition_false_branch():
    workflow = {
        "id": "wf_cond_false",
        "nodes": [
            {"id": "n_in", "type": "Input", "name": "Score Input", "config": {}},
            {
                "id": "n_cond",
                "type": "Condition",
                "name": "Check Threshold",
                "config": {"operator": ">=", "value": 80},
            },
            {"id": "n_true", "type": "Output", "name": "Pass Node", "config": {}},
            {"id": "n_false", "type": "Output", "name": "Fail Node", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n_in", "target": "n_cond"},
            {"id": "e_true", "source": "n_cond", "target": "n_true", "sourceHandle": "true"},
            {"id": "e_false", "source": "n_cond", "target": "n_false", "sourceHandle": "false"},
        ],
    }

    report = await execution_engine.execute(workflow, {"n_in": 45})
    assert report.status == ExecutionStatus.SUCCESS
    logs_by_id = {l.node_id: l.status for l in report.node_logs}
    assert logs_by_id["n_true"] == ExecutionStatus.SKIPPED
    assert logs_by_id["n_false"] == ExecutionStatus.SUCCESS


# -------------------------------------------------------------------------
# 7. Human Approval waiting state
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_human_approval_waiting_state():
    workflow = {
        "id": "wf_approval",
        "nodes": [
            {"id": "n_in", "type": "Input", "name": "Application Data", "config": {}},
            {"id": "n_gate", "type": "Human Approval", "name": "Manager Approval", "config": {}},
            {"id": "n_out", "type": "Output", "name": "Final Dispatch", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n_in", "target": "n_gate"},
            {"id": "e2", "source": "n_gate", "target": "n_out"},
        ],
    }

    report = await execution_engine.execute(workflow, {"n_in": "Candidate payload"})
    assert report.status == ExecutionStatus.WAITING_FOR_APPROVAL
    assert report.waiting_node_id == "n_gate"


# -------------------------------------------------------------------------
# 8. Human Approval and resume
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_human_approval_and_resume():
    workflow = {
        "id": "wf_approval_resume",
        "nodes": [
            {"id": "n_in", "type": "Input", "name": "Application Data", "config": {}},
            {"id": "n_gate", "type": "Human Approval", "name": "Manager Approval", "config": {}},
            {"id": "n_out", "type": "Output", "name": "Final Dispatch", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n_in", "target": "n_gate"},
            {"id": "e2", "source": "n_gate", "target": "n_out"},
        ],
    }

    ctx = ExecutionContext(
        workflow_id="wf_approval_resume",
        execution_id="exec-app-1",
        inputs={"n_in": "Approved candidate data"},
        waiting_node_id="n_gate",
    )
    ctx.completed_nodes.add("n_in")
    ctx.node_outputs["n_in"] = {"output": "Approved candidate data"}

    resume_report = await execution_engine.resume_after_approval(
        workflow=workflow,
        context=ctx,
        action="approve",
        comment="Looks great!",
    )

    assert resume_report.status == ExecutionStatus.SUCCESS
    assert resume_report.result is not None


# -------------------------------------------------------------------------
# 9. Human Approval rejection
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_human_approval_rejection():
    workflow = {
        "id": "wf_approval_rej",
        "nodes": [
            {"id": "n_in", "type": "Input", "name": "Application Data", "config": {}},
            {"id": "n_gate", "type": "Human Approval", "name": "Manager Approval", "config": {}},
            {"id": "n_out", "type": "Output", "name": "Final Dispatch", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n_in", "target": "n_gate"},
            {"id": "e2", "source": "n_gate", "target": "n_out"},
        ],
    }

    ctx = ExecutionContext(
        workflow_id="wf_approval_rej",
        execution_id="exec-app-2",
        inputs={"n_in": "Candidate data"},
        waiting_node_id="n_gate",
    )

    report = await execution_engine.resume_after_approval(
        workflow=workflow,
        context=ctx,
        action="reject",
        comment="Candidate requirements not met.",
    )

    assert report.status == ExecutionStatus.REJECTED
    assert "rejected" in str(report.error_message).lower()


# -------------------------------------------------------------------------
# 10. Missing input validation
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_missing_input_validation():
    workflow = {
        "id": "wf_missing_input",
        "nodes": [
            {"id": "n_in", "type": "Input", "name": "Mandatory Input", "config": {"required": True}},
            {"id": "n_out", "type": "Output", "name": "Result", "config": {}},
        ],
        "edges": [{"id": "e1", "source": "n_in", "target": "n_out"}],
    }

    report = await execution_engine.execute(workflow, {})
    assert report.status == ExecutionStatus.FAILED
    assert "missing" in str(report.error_message).lower()
    assert report.failed_node_id == "n_in"


# -------------------------------------------------------------------------
# 11. Unsupported node type
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unsupported_node_type():
    workflow = {
        "id": "wf_unsupported",
        "nodes": [
            {"id": "n1", "type": "AlienNodeReactor", "name": "Unknown", "config": {}},
        ],
        "edges": [],
    }

    report = await execution_engine.execute(workflow, {})
    assert report.status == ExecutionStatus.FAILED
    assert "unsupported" in str(report.error_message).lower()


# -------------------------------------------------------------------------
# 12. Invalid connections (edge points to missing node)
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_invalid_connections():
    workflow = {
        "id": "wf_invalid_edge",
        "nodes": [
            {"id": "n1", "type": "Input", "name": "Input 1", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "ghost_node"},
        ],
    }

    with pytest.raises(WorkflowValidationError):
        await execution_engine.execute(workflow, {})


# -------------------------------------------------------------------------
# 13. Cyclic workflow detection
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_cyclic_workflow_detection():
    workflow = {
        "id": "wf_cycle",
        "nodes": [
            {"id": "node_a", "type": "Input", "name": "A", "config": {}},
            {"id": "node_b", "type": "Tool", "name": "B", "config": {"toolName": "calculator"}},
        ],
        "edges": [
            {"id": "e1", "source": "node_a", "target": "node_b"},
            {"id": "e2", "source": "node_b", "target": "node_a"},
        ],
    }

    with pytest.raises(CycleDetectedError):
        await execution_engine.execute(workflow, {})


# -------------------------------------------------------------------------
# 14. Failed node execution handling
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_failed_node_execution():
    workflow = {
        "id": "wf_failed_node",
        "nodes": [
            {"id": "n1", "type": "Input", "name": "Input", "config": {}},
            {"id": "n2", "type": "Tool", "name": "Calculator Fail", "config": {"toolName": "calculator"}},
            {"id": "n3", "type": "Output", "name": "Output", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
        ],
    }

    # Zero division in calculator
    report = await execution_engine.execute(workflow, {"n1": {"expression": "100 / 0"}})
    assert report.status == ExecutionStatus.FAILED
    assert report.failed_node_id == "n2"
    assert "division by zero" in str(report.error_message).lower()


# -------------------------------------------------------------------------
# 15. Multiple-node data passing
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_multiple_node_data_passing():
    workflow = {
        "id": "wf_multi_pass",
        "nodes": [
            {"id": "step1", "type": "Input", "name": "Raw String", "config": {}},
            {"id": "step2", "type": "Tool", "name": "Uppercase", "config": {"toolName": "text_formatter", "operation": "upper"}},
            {"id": "step3", "type": "Output", "name": "Final Result", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "step1", "target": "step2"},
            {"id": "e2", "source": "step2", "target": "step3"},
        ],
    }

    report = await execution_engine.execute(workflow, {"step1": "agentforge visual engine"})
    assert report.status == ExecutionStatus.SUCCESS
    assert "AGENTFORGE VISUAL ENGINE" in str(report.result)


# -------------------------------------------------------------------------
# 16. Execution logs recording
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_execution_logs():
    workflow = {
        "id": "wf_logs",
        "nodes": [
            {"id": "n1", "type": "Input", "name": "Input Step", "config": {}},
            {"id": "n2", "type": "Output", "name": "Output Step", "config": {}},
        ],
        "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
    }

    report = await execution_engine.execute(workflow, {"n1": "trace verification"})
    assert len(report.node_logs) == 2
    for log in report.node_logs:
        assert log.node_id in ("n1", "n2")
        assert log.start_time is not None
        assert log.end_time is not None
        assert log.status == ExecutionStatus.SUCCESS


# -------------------------------------------------------------------------
# 17. Node-level execution time tracking
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_node_level_execution_time():
    workflow = {
        "id": "wf_timings",
        "nodes": [
            {"id": "n_in", "type": "Input", "name": "Timing In", "config": {}},
            {"id": "n_out", "type": "Output", "name": "Timing Out", "config": {}},
        ],
        "edges": [{"id": "e1", "source": "n_in", "target": "n_out"}],
    }

    report = await execution_engine.execute(workflow, {"n_in": "test"})
    assert "n_in" in report.metrics.node_durations_ms
    assert "n_out" in report.metrics.node_durations_ms
    assert report.metrics.node_durations_ms["n_in"] >= 0.0


# -------------------------------------------------------------------------
# 18. Complete workflow execution time tracking
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_complete_workflow_execution_time():
    workflow = {
        "id": "wf_total_time",
        "nodes": [
            {"id": "n1", "type": "Input", "name": "Start", "config": {}},
            {"id": "n2", "type": "Output", "name": "End", "config": {}},
        ],
        "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
    }

    report = await execution_engine.execute(workflow, {"n1": "speed"})
    assert report.metrics.total_duration_ms >= 0.0
    assert report.total_duration_ms == report.metrics.total_duration_ms


# -------------------------------------------------------------------------
# 19. API call and token usage capture
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_api_call_and_token_usage_capture():
    workflow = {
        "id": "wf_token_capture",
        "nodes": [
            {"id": "in1", "type": "Input", "name": "Query In", "config": {}},
            {"id": "llm1", "type": "LLM", "name": "AI Model", "config": {"apiKey": "gemini-key-test"}},
            {"id": "out1", "type": "Output", "name": "Result Out", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "in1", "target": "llm1"},
            {"id": "e2", "source": "llm1", "target": "out1"},
        ],
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Synthesized insights."}]}}],
        "usageMetadata": {"promptTokenCount": 110, "candidatesTokenCount": 45, "totalTokenCount": 155},
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        report = await execution_engine.execute(workflow, {"in1": "Token counting test."})

    assert report.metrics.total_api_calls == 1
    assert report.metrics.total_token_usage.prompt_tokens == 110
    assert report.metrics.total_token_usage.completion_tokens == 45
    assert report.metrics.total_token_usage.total_tokens == 155


# -------------------------------------------------------------------------
# 20. Controlled re-execution after repair
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_controlled_reexecution_after_repair():
    # Repaired workflow with valid expression replacing zero-division
    repaired_workflow = {
        "id": "wf_repaired",
        "nodes": [
            {"id": "n1", "type": "Input", "name": "Input", "config": {}},
            {"id": "n2", "type": "Tool", "name": "Repaired Calc", "config": {"toolName": "calculator"}},
            {"id": "n3", "type": "Output", "name": "Output", "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
        ],
    }

    report = await execution_engine.execute(
        repaired_workflow,
        {"n1": {"expression": "100 / 2"}},
        reexecution=True,
        original_duration_ms=10.0,
    )

    assert report.status == ExecutionStatus.SUCCESS
    assert report.result["result"]["result"] == 50.0
    assert report.metrics.reexecution_overhead_ms is not None
