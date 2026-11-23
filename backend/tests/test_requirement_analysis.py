"""Automated test suite for Member 2: AI Requirement Analysis & Agent Architect.

Tests:
1. Natural-language requirement analysis
2. Requirement extraction (inputs, processing, outputs, tools, constraints)
3. Task decomposition (task_id, ordering, dependencies, component)
4. Canonical component identification (7 supported types strictly)
5. Missing requirement detection & clarification question generation
6. Clarification answer resolution into ready execution plan
7. Valid JSON output & Pydantic schema validation
8. Resilient handling of invalid/incomplete Gemini responses
9. FastAPI endpoint POST /api/v1/agents/analyze
10. LangGraph StateGraph workflow execution and node routing
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.requirement_analysis_service import (
    RequirementAnalysisService,
    requirement_graph,
    _detect_missing_and_clarifications,
)
from app.agents.requirement_analysis_agent import RequirementAnalysisAgent
from app.schemas.requirement_analysis import (
    ExecutionPlanResponse,
    SUPPORTED_COMPONENTS_LIST,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. LangGraph StateGraph Structure Tests
# ---------------------------------------------------------------------------
def test_langgraph_nodes_registered():
    """Verify all 7 required nodes are present in the compiled StateGraph."""
    graph_nodes = requirement_graph.nodes
    expected_nodes = [
        "requirement_input",
        "requirement_analysis",
        "task_decomposition",
        "component_selection",
        "requirement_validation",
        "planning",
        "output",
    ]
    for node_name in expected_nodes:
        assert node_name in graph_nodes, f"Node '{node_name}' missing from LangGraph StateGraph"


# ---------------------------------------------------------------------------
# 2. Natural-Language Analysis & Clear Prompt Execution
# ---------------------------------------------------------------------------
def test_requirement_analysis_clear_prompt():
    """Verify complete requirement analysis and task decomposition for illustrative prompt."""
    service = RequirementAnalysisService()
    prompt = (
        "Create an AI agent that reads PDF resumes, extracts candidate skills, "
        "compares them with a job description, and generates an evaluation report."
    )

    plan: ExecutionPlanResponse = service.analyze_requirements(description=prompt)

    # 1. Objective & Status
    assert plan.status == "ready"
    assert "candidate" in plan.project_objective.lower() or "resume" in plan.project_objective.lower()

    # 2. Extracted Requirements
    assert len(plan.requirements.inputs) >= 1
    assert any("resume" in i.lower() or "pdf" in i.lower() for i in plan.requirements.inputs)
    assert len(plan.requirements.processing) >= 3
    assert len(plan.requirements.outputs) >= 1
    assert any("report" in o.lower() for o in plan.requirements.outputs)

    # 3. Task Decomposition
    assert len(plan.tasks) >= 3
    for idx, task in enumerate(plan.tasks, start=1):
        assert task.task_id.startswith("T")
        assert task.execution_order == idx
        assert task.component in SUPPORTED_COMPONENTS_LIST
        assert task.required_component == task.component
        assert isinstance(task.dependencies, list)

    # 4. Canonical Components
    assert "Input" in plan.required_components
    assert "LLM" in plan.required_components
    assert "Output" in plan.required_components
    for comp in plan.required_components:
        assert comp in SUPPORTED_COMPONENTS_LIST

    # 5. Clarifications empty for clear prompt
    assert len(plan.clarification_questions) == 0


# ---------------------------------------------------------------------------
# 3. Missing Requirement Detection & Clarification Questions
# ---------------------------------------------------------------------------
def test_missing_requirement_detection():
    """Verify ambiguous prompt triggers clarification questions with reasons."""
    service = RequirementAnalysisService()
    vague_prompt = "Make a bot"

    plan: ExecutionPlanResponse = service.analyze_requirements(description=vague_prompt)

    assert plan.status == "needs_clarification"
    assert len(plan.clarification_questions) >= 1
    for q in plan.clarification_questions:
        assert q.id.startswith("Q")
        assert len(q.question) > 10
        assert len(q.reason) > 10
        assert "clarification is needed" in q.reason.lower()


def test_clarification_resolution_flow():
    """Verify submitting clarification answers turns needs_clarification into ready plan."""
    service = RequirementAnalysisService()
    vague_prompt = "Make an evaluation bot"

    # Step 1: Without answers -> needs clarification
    plan1 = service.analyze_requirements(description=vague_prompt)
    assert plan1.status == "needs_clarification"
    assert len(plan1.clarification_questions) > 0

    # Step 2: With clarification answers -> ready
    answers = {
        "Q1": "Uploaded PDF documents containing candidate CVs",
        "Q2": "Markdown evaluation scorecard",
        "Q3": "Candidate must meet 70% skill overlap score",
    }
    plan2 = service.analyze_requirements(description=vague_prompt, clarification_answers=answers)
    assert plan2.status == "ready"
    assert len(plan2.clarification_questions) == 0
    assert len(plan2.tasks) >= 3


# ---------------------------------------------------------------------------
# 4. Strict Component Identification (No Unsupported Components)
# ---------------------------------------------------------------------------
def test_component_identification_strictness():
    """Verify that only the 7 canonical components are ever assigned."""
    service = RequirementAnalysisService()
    prompts = [
        "Parse invoice receipt and store line items in PostgreSQL database with Slack notification",
        "Answer questions from company manuals and ask human manager for approval before answering",
        "Summarize news articles and format into JSON summary",
    ]

    for p in prompts:
        plan = service.analyze_requirements(description=p)
        for task in plan.tasks:
            assert task.component in SUPPORTED_COMPONENTS_LIST, f"Unsupported component {task.component} in task {task.task_id}"
        for comp in plan.required_components:
            assert comp in SUPPORTED_COMPONENTS_LIST, f"Unsupported component {comp}"


# ---------------------------------------------------------------------------
# 5. Gemini API Integration & Resilient Fallback
# ---------------------------------------------------------------------------
def test_gemini_integration_mocked_success():
    """Verify integration when Gemini returns valid structured JSON."""
    mock_gemini_response = {
        "project_objective": "Automated Invoice Auditing System",
        "inputs": ["PDF Invoices", "ERP Purchase Orders"],
        "processing": ["Extract line items", "Calculate tax totals", "Audit variances"],
        "outputs": ["Audit Exception Report"],
        "tools": ["ERP API"],
        "constraints": ["Variance threshold <= $50"],
    }

    with patch("app.services.requirement_analysis_service.call_gemini_json", return_value=mock_gemini_response):
        service = RequirementAnalysisService()
        plan = service.analyze_requirements("Audit vendor invoices against ERP purchase orders")

        assert plan.project_objective == "Automated Invoice Auditing System"
        assert "PDF Invoices" in plan.requirements.inputs
        assert "Audit Exception Report" in plan.requirements.outputs
        assert plan.status == "ready"


def test_gemini_integration_invalid_response_fallback():
    """Verify system remains resilient when Gemini returns None or invalid payload."""
    with patch("app.services.requirement_analysis_service.call_gemini_json", return_value=None):
        service = RequirementAnalysisService()
        plan = service.analyze_requirements(
            "Create an AI agent that reads PDF resumes, extracts candidate skills, compares them with a job description, and generates an evaluation report."
        )

        assert plan.status == "ready"
        assert len(plan.tasks) >= 3
        assert "candidate" in plan.project_objective.lower() or "evaluate" in plan.project_objective.lower()


# ---------------------------------------------------------------------------
# 6. FastAPI Endpoint Tests: POST /api/v1/agents/analyze
# ---------------------------------------------------------------------------
def test_api_analyze_endpoint_success():
    """Verify HTTP POST /api/v1/agents/analyze returns valid 200 execution plan."""
    payload = {
        "description": "Create an AI agent that reads PDF resumes, extracts candidate skills, compares with job descriptions and produces a scorecard.",
        "clarification_answers": {},
    }
    response = client.post("/api/v1/agents/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "project_objective" in data
    assert data["status"] == "ready"
    assert "requirements" in data
    assert "inputs" in data["requirements"]
    assert "processing" in data["requirements"]
    assert "outputs" in data["requirements"]
    assert "tasks" in data
    assert len(data["tasks"]) >= 3
    assert "required_components" in data
    assert "contract_version" in data


def test_api_analyze_endpoint_validation_error():
    """Verify HTTP 400 Bad Request when description is empty or too short."""
    response = client.post("/api/v1/agents/analyze", json={"description": ""})
    assert response.status_code in (400, 422)

    response_short = client.post("/api/v1/agents/analyze", json={"description": "ab"})
    assert response_short.status_code in (400, 422)


def test_api_analyze_with_clarifications():
    """Verify API endpoint handles clarification question answers correctly."""
    payload = {
        "description": "Evaluate candidates",
        "clarification_answers": {
            "Q1": "Uploaded PDF resumes",
            "Q2": "Scorecard report",
        },
    }
    response = client.post("/api/v1/agents/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert len(data["tasks"]) >= 3


# ---------------------------------------------------------------------------
# 7. Member 3 Contract Adherence
# ---------------------------------------------------------------------------
def test_member_3_contract_structure():
    """Verify execution plan JSON adheres precisely to Member 3 contract."""
    agent = RequirementAnalysisAgent()
    plan = agent.analyze(
        "Create an AI agent that reads PDF resumes, extracts candidate skills, compares them with a job description, and generates an evaluation report."
    )
    plan_dict = plan.model_dump()

    # Exact expected fields
    assert "project_objective" in plan_dict
    assert "status" in plan_dict
    assert "requirements" in plan_dict
    assert "tasks" in plan_dict
    assert "clarification_questions" in plan_dict

    # Check task fields
    first_task = plan_dict["tasks"][0]
    assert "task_id" in first_task
    assert "task_name" in first_task
    assert "component" in first_task
    assert "execution_order" in first_task
    assert "dependencies" in first_task
    assert "input" in first_task
    assert "expected_output" in first_task

    # Verify no React Flow nodes or edges were generated (Member 3 responsibility)
    assert "nodes" not in plan_dict
    assert "edges" not in plan_dict
