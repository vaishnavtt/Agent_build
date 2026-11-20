import pytest
from app.agents.planner_agent import PlannerAgent
from app.agents.research_agent import ResearchAgent
from app.agents.validation_agent import ValidationAgent
from app.agents.execution_agent import ExecutionAgent
from app.agents.error_detection_agent import ErrorDetectionAgent
from app.agents.self_repair_agent import SelfRepairAgent


def test_planner_agent_plan_workflow():
    agent = PlannerAgent()
    result = agent.plan_workflow("Build an invoice extraction agent")
    assert "nodes" in result
    assert "edges" in result
    assert len(result["nodes"]) >= 3
    assert any("invoice" in n.get("data", {}).get("label", "").lower() for n in result["nodes"])


def test_research_agent_collect_and_extract():
    agent = ResearchAgent()
    res = agent.collect_information("candidate skills evaluation")
    assert res["status"] == "completed"
    assert "summary" in res

    doc_res = agent.extract_document_data(
        "Candidate has extensive experience in React, TypeScript, Python and Docker.",
        doc_type="pdf",
    )
    assert "React" in doc_res["detected_skills"]
    assert "TypeScript" in doc_res["detected_skills"]
    assert "Python" in doc_res["detected_skills"]


def test_validation_agent_validates_graph():
    agent = ValidationAgent()
    nodes = [
        {"id": "n1", "type": "customWorkflow", "data": {"label": "Start", "componentType": "Input"}},
        {"id": "n2", "type": "customWorkflow", "data": {"label": "LLM Step", "componentType": "LLM", "config": {"instructions": "Score candidate."}}},
        {"id": "n3", "type": "customWorkflow", "data": {"label": "End", "componentType": "Output"}},
    ]
    edges = [
        {"id": "e1", "source": "n1", "target": "n2"},
        {"id": "e2", "source": "n2", "target": "n3"},
    ]
    result = agent.validate_workflow(nodes, edges)
    assert result["is_valid"] is True
    assert result["readiness_score"] >= 90


def test_validation_agent_catches_missing_config():
    agent = ValidationAgent()
    nodes = [
        {"id": "n1", "type": "customWorkflow", "data": {"label": "Start", "componentType": "Input"}},
        {"id": "n2", "type": "customWorkflow", "data": {"label": "Empty LLM", "componentType": "LLM", "config": {"instructions": ""}}},
        {"id": "n3", "type": "customWorkflow", "data": {"label": "End", "componentType": "Output"}},
    ]
    edges = [
        {"id": "e1", "source": "n1", "target": "n2"},
        {"id": "e2", "source": "n2", "target": "n3"},
    ]
    result = agent.validate_workflow(nodes, edges)
    assert result["is_valid"] is False
    assert any("Missing Instructions" in i["title"] for i in result["issues"])


def test_error_detection_and_self_repair_pipeline():
    err_agent = ErrorDetectionAgent()
    repair_agent = SelfRepairAgent()

    workflow = {
        "name": "Faulty Workflow",
        "nodes": [
            {"id": "n1", "data": {"label": "Upload", "componentType": "Input"}},
            {"id": "n2", "data": {"label": "Evaluate Fit", "componentType": "LLM", "config": {"instructions": ""}}},
            {"id": "n3", "data": {"label": "Report", "componentType": "Output"}},
        ],
        "edges": [{"source": "n1", "target": "n2"}, {"source": "n2", "target": "n3"}],
    }
    steps = [
        {"id": "step-n1", "componentName": "Upload", "componentType": "Input", "status": "completed"},
        {"id": "step-n2", "componentName": "Evaluate Fit", "componentType": "LLM", "status": "failed"},
    ]

    diagnosis = err_agent.diagnose_failure(workflow, steps)
    assert "instructions" in diagnosis["problemFound"].lower()
    assert len(diagnosis["logEvidence"]) > 0

    repair_result = repair_agent.repair_workflow(workflow, diagnosis, attempt_number=1)
    assert repair_result["success"] is True
    assert repair_result["repair_report"]["finalStatus"] == "VERIFIED_SUCCESS"

    # Verify repaired workflow node now has instructions
    repaired_nodes = repair_result["repaired_workflow"]["nodes"]
    llm_node = next(n for n in repaired_nodes if n["id"] == "n2")
    assert len(llm_node["data"]["config"]["instructions"]) > 10
