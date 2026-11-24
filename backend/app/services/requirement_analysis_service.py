"""Requirement Analysis Service - LangGraph AI Planning Workflow for Member 2.

Implements:
1. Requirement Input Node
2. Requirement Analysis Node
3. Task Decomposition Node
4. Component Selection Node
5. Requirement Validation Node
6. Planning Node
7. Output Node
Connected via LangGraph StateGraph with conditional routing for clarification.
"""

from typing import List, Dict, Any, Optional, TypedDict
import json
import logging
import re
from langgraph.graph import StateGraph, START, END

from app.schemas.requirement_analysis import (
    SupportedComponent,
    SUPPORTED_COMPONENTS_LIST,
    TaskDecompositionItem,
    RequirementsBreakdown,
    AcceptanceCriterion,
    EdgeCaseScenario,
    TestScenario,
    ClarificationQuestion,
    ExecutionPlanResponse,
)
from app.core.gemini_client import call_gemini_json
from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LangGraph State Definition
# ---------------------------------------------------------------------------
class RequirementAnalysisState(TypedDict, total=False):
    """Shared state dictionary passed across LangGraph nodes."""

    # Input state
    description: str
    clarification_answers: Dict[str, str]
    context: Dict[str, Any]

    # Analysis state
    project_objective: str
    requirements: Dict[str, Any]  # inputs, processing, outputs, tools, constraints, functional, non_functional
    ai_provider: str  # "google-gemini" | "deterministic_engine" | "mock"
    model_used: Optional[str]

    # Task decomposition state
    tasks: List[Dict[str, Any]]

    # Component selection state
    selected_components: List[str]

    # Validation state
    is_valid: bool
    status: str  # "ready" | "needs_clarification"
    clarification_questions: List[Dict[str, Any]]
    validation_notes: List[str]

    # Extended synthesis state
    acceptance_criteria: List[Dict[str, Any]]
    edge_cases: List[Dict[str, Any]]
    test_scenarios: List[Dict[str, Any]]
    assumptions: List[str]

    # Planning state
    architecture_summary: str
    confidence_score: float

    # Output state
    final_plan: Dict[str, Any]
    errors: List[str]


# ---------------------------------------------------------------------------
# Semantic Heuristic Fallback Engine
# (Ensures 100% resilient operation when offline, mocked, or without API key)
# ---------------------------------------------------------------------------
def _has_keyword(text: str, keywords: List[str]) -> bool:
    """Checks if any keyword matches as a distinct word or substring if keyword > 3 chars."""
    t_lower = text.lower()
    for kw in keywords:
        kw_l = kw.lower()
        if len(kw_l) <= 3:
            # Word boundary check for short abbreviations like 'cv', 'po', 'doc', 'qa'
            if re.search(r"\b" + re.escape(kw_l) + r"\b", t_lower):
                return True
        else:
            if kw_l in t_lower:
                return True
    return False


def _detect_missing_and_clarifications(
    prompt: str,
    clarification_answers: Dict[str, str],
    extracted_requirements: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Detects missing or ambiguous requirements and returns clarification questions.
    Checks user prompt, existing clarification answers, and extracted requirements.
    """
    p_lower = prompt.lower().strip()
    words = p_lower.split()
    questions: List[Dict[str, Any]] = []

    req = extracted_requirements or {}
    inputs = [i for i in req.get("inputs", []) if i.strip() and i != "User input data"]
    outputs = [o for o in req.get("outputs", []) if o.strip() and o != "Structured output report"]

    has_input_answer = any(
        ("q1" in k.lower() or "input" in k.lower() or "source" in k.lower() or "doc" in k.lower())
        and bool(v.strip())
        for k, v in clarification_answers.items()
    )
    has_output_answer = any(
        ("q2" in k.lower() or "output" in k.lower() or "format" in k.lower() or "deliverable" in k.lower())
        and bool(v.strip())
        for k, v in clarification_answers.items()
    )

    mentions_source = any(w in p_lower for w in [
        "pdf", "resume", "cv", "invoice", "document", "doc", "file", "upload",
        "text", "csv", "email", "url", "webhook", "receipt", "contract", "orders", "manual"
    ])
    mentions_outcome = any(w in p_lower for w in [
        "report", "score", "summary", "decision", "notify", "output", "export",
        "dashboard", "scorecard", "evaluation report", "result", "audit", "answers"
    ])

    # If the user prompt is extremely short or lacks inputs/outputs
    if len(words) < 6 or (not mentions_source and not mentions_outcome):
        if not mentions_source and not has_input_answer and not inputs:
            questions.append({
                "id": "Q1",
                "question": "What is the primary input source or document type (e.g., uploaded PDF resumes, invoices, API payloads, or plain text)?",
                "reason": "Clarification is needed to select appropriate document readers and input validation components without generating an unreliable plan.",
                "category": "input_source"
            })
        if not mentions_outcome and not has_output_answer and not outputs:
            questions.append({
                "id": "Q2",
                "question": "What is the desired final output format (e.g., candidate evaluation report, scorecard, markdown summary, or structured JSON)?",
                "reason": "Clarification is needed to configure the terminal output sinks and formatting requirements.",
                "category": "output_format"
            })

    return questions


def _heuristic_requirement_analysis(
    description: str,
    clarification_answers: Dict[str, str],
) -> Dict[str, Any]:
    """Generates structured analysis using deterministic semantic heuristics."""
    p_lower = description.lower()
    words = description.strip().split()

    mentions_source = any(w in p_lower for w in [
        "pdf", "resume", "cv", "invoice", "document", "doc", "file", "upload",
        "text", "csv", "email", "url", "webhook", "receipt", "contract", "orders", "manual"
    ])
    mentions_outcome = any(w in p_lower for w in [
        "report", "score", "summary", "decision", "notify", "output", "export",
        "dashboard", "scorecard", "evaluation", "result", "audit", "answers"
    ])

    # If prompt is extremely vague and no answers provided yet
    if (len(words) < 5 or (not mentions_source and not mentions_outcome)) and not clarification_answers:
        return {
            "project_objective": description.strip(),
            "inputs": [],
            "processing": ["Awaiting clarification to determine processing requirements"],
            "outputs": [],
            "tools": [],
            "constraints": ["Requirements pending user clarification"],
        }

    # Detect domain with word-boundary awareness
    is_weather = _has_keyword(p_lower, ["weather", "temperature", "humidity", "wind", "forecast", "climate"])
    is_resume = _has_keyword(p_lower, ["resume", "candidate", "applicant", "hire", "recruiting", "cv"])
    is_invoice = _has_keyword(p_lower, ["invoice", "receipt", "bill", "vendor", "po", "purchase order", "audit"])
    is_support = _has_keyword(p_lower, ["ticket", "support", "customer service", "email triage", "inquiry"])
    is_qa = _has_keyword(p_lower, ["question", "answer", "q&a", "manual", "knowledge"])
    is_summary = _has_keyword(p_lower, ["summar", "bullet", "digest", "brief"])

    # Inputs
    inputs = []
    if is_weather:
        inputs = ["Temperature reading", "Humidity percentage", "Wind speed measurement"]
    elif is_resume:
        inputs = ["PDF resume", "Job description"]
    elif is_invoice:
        inputs = ["Invoice PDF / Image", "Purchase Order specifications"]
    elif is_support:
        inputs = ["Customer support message / email payload", "Ticket metadata"]
    elif is_qa:
        inputs = ["PDF knowledge documents", "User question prompt"]
    elif is_summary:
        inputs = ["Source documents (PDF / DOCX / TXT)"]
    else:
        if "pdf" in p_lower:
            inputs.append("PDF document")
        if "job" in p_lower:
            inputs.append("Job description")
        if not inputs:
            inputs.append("User input data")

    # Merge answers if provided
    for q_id, ans in clarification_answers.items():
        if ans and ("input" in q_id.lower() or "q1" in q_id.lower() or "source" in q_id.lower()):
            inputs = [ans.strip()]

    # Processing requirements
    processing = []
    if is_weather:
        processing = [
            "Ingest environmental sensor data",
            "Validate atmospheric parameter bounds",
            "Analyze weather conditions with LLM model",
            "Evaluate weather condition thresholds (sunny, rainy, stormy)",
            "Synthesize weather prediction report"
        ]
    elif is_resume:
        processing = [
            "Extract resume information",
            "Extract candidate skills",
            "Analyze job description",
            "Compare candidate skills",
            "Evaluate candidate suitability"
        ]
    elif is_invoice:
        processing = [
            "Extract invoice text and layout",
            "Parse line items, totals, and tax",
            "Verify totals against purchase order rules",
            "Perform compliance threshold check",
            "Generate invoice audit report"
        ]
    elif is_support:
        processing = [
            "Ingest customer support message",
            "Classify intent, urgency, and sentiment with LLM",
            "Evaluate escalation condition (high priority vs standard resolution)",
            "Generate automated response or dispatch to support queue"
        ]
    elif is_qa:
        processing = [
            "Ingest and chunk knowledge document",
            "Index content for semantic search",
            "Analyze user question",
            "Retrieve relevant excerpts",
            "Synthesize answer with citations"
        ]
    elif is_summary:
        processing = [
            "Read and parse document content",
            "Identify key themes and metrics",
            "Generate executive bullet summaries",
            "Format final document digest"
        ]
    else:
        processing = [
            "Ingest input parameters",
            "Process content with AI model",
            "Validate results against constraints",
            "Synthesize final deliverable"
        ]

    # Incorporate answers if present
    for q_id, ans in clarification_answers.items():
        if ans and len(ans.strip()) > 0 and not ("q1" in q_id.lower() or "q2" in q_id.lower()):
            processing.append(f"Apply clarified criteria: {ans.strip()}")

    # Outputs
    outputs = []
    if is_weather:
        outputs = ["Weather prediction report"]
    elif is_resume:
        outputs = ["Candidate evaluation report"]
    elif is_invoice:
        outputs = ["Verified invoice record and approval status"]
    elif is_support:
        outputs = ["Automated response / triage ticket assignment"]
    elif is_qa:
        outputs = ["Answer with document citations"]
    elif is_summary:
        outputs = ["Executive summary report"]
    else:
        outputs = ["Structured output report"]

    for q_id, ans in clarification_answers.items():
        if ans and ("output" in q_id.lower() or "q2" in q_id.lower() or "format" in q_id.lower()):
            outputs = [ans.strip()]

    # Tools
    tools = []
    if "email" in p_lower or "send" in p_lower:
        tools.append("Email notification tool")
    if "slack" in p_lower:
        tools.append("Slack notification webhook")
    if "db" in p_lower or "database" in p_lower or "save" in p_lower or "store" in p_lower:
        tools.append("Database storage tool")
    if "erp" in p_lower or "api" in p_lower:
        tools.append("ERP API sync integration")

    # Constraints
    constraints = []
    if is_weather:
        constraints = [
            "Ensure humidity is in range [0, 100]% and wind speed >= 0",
            "Generate structured markdown prediction report"
        ]
    elif "score" in p_lower or "threshold" in p_lower:
        constraints.append("Apply pass/fail threshold evaluation")
    if "approval" in p_lower or "human" in p_lower:
        constraints.append("Require human manager sign-off")
    if not constraints:
        constraints.append("Ensure schema adherence and execution safety")

    # Functional & Non-Functional
    if is_weather:
        functional = [
            "Ingest numerical weather metrics (temperature, humidity, wind speed)",
            "Validate parameters against physical atmospheric bounds",
            "Predict weather conditions and risk flags using AI model",
            "Generate structured weather prediction report deliverable"
        ]
        non_functional = [
            "Prediction response latency under 2.0 seconds",
            "Input boundary validation prevents anomalous sensor processing",
            "Adherence to supported workflow component primitives"
        ]
    elif is_resume:
        functional = [
            "Extract candidate skills and experience from PDF resumes",
            "Extract requirements and qualifications from job descriptions",
            "Perform semantic skill comparison and gap analysis",
            "Generate structured candidate evaluation report with scoring"
        ]
        non_functional = [
            "Document parsing handles PDFs up to 20MB",
            "Execution order guarantees upstream data before LLM reasoning",
            "Strict adherence to canonical component primitives"
        ]
    elif is_support:
        functional = [
            "Ingest incoming customer support inquiries and emails",
            "Classify request urgency, category, and customer sentiment",
            "Route critical or negative tickets to human team for approval",
            "Generate and dispatch automated resolution responses"
        ]
        non_functional = [
            "Ticket triage and response latency under 1.5 seconds",
            "Strict adherence to 7 canonical components"
        ]
    elif is_qa:
        functional = [
            "Parse knowledge manuals and reference documents",
            "Extract relevant context passages matching user questions",
            "Synthesize factual answers with source citations"
        ]
        non_functional = [
            "Response latency under 2.0 seconds",
            "Strict adherence to canonical components"
        ]
    else:
        functional = [
            f"Process user inputs for '{description.strip()[:60]}'",
            "Apply AI reasoning model to transform and evaluate data",
            "Format final response deliverable"
        ]
        non_functional = [
            "Workflow execution follows topological dependency order",
            "Fault-tolerant error handling on malformed inputs",
            "Strict adherence to 7 canonical components"
        ]

    # Objective
    if is_weather:
        objective = "Predict weather conditions using temperature, humidity, and wind speed"
    elif is_resume:
        objective = "Evaluate candidates using resumes and job descriptions"
    elif is_invoice:
        objective = "Extract, validate, and process invoice data against compliance rules"
    elif is_support:
        objective = "Triage customer support requests and dispatch automated responses"
    elif is_qa:
        objective = "Answer user questions accurately from parsed knowledge documents"
    elif is_summary:
        objective = "Summarize lengthy documents into concise executive takeaways"
    else:
        clean_desc = description.strip()
        objective = clean_desc if len(clean_desc) <= 80 else f"{clean_desc[:77]}..."

    return {
        "project_objective": objective,
        "inputs": inputs,
        "processing": processing,
        "outputs": outputs,
        "tools": tools,
        "constraints": constraints,
        "functional": functional,
        "non_functional": non_functional,
    }


def _heuristic_acceptance_criteria(
    objective: str,
    requirements: Dict[str, Any],
    description: str,
) -> List[Dict[str, Any]]:
    p_lower = description.lower()
    is_weather = _has_keyword(p_lower, ["weather", "temperature", "humidity", "wind", "forecast", "climate"])
    is_resume = _has_keyword(p_lower, ["resume", "candidate", "applicant", "hire", "recruiting", "cv"])
    is_invoice = _has_keyword(p_lower, ["invoice", "receipt", "bill", "vendor", "po", "purchase order", "audit"])
    is_support = _has_keyword(p_lower, ["ticket", "support", "customer service", "email triage", "inquiry"])

    if is_weather:
        return [
            {
                "id": "AC1",
                "requirement_id": "FR1",
                "criteria": "System must ingest temperature, humidity, and wind speed inputs.",
                "description": "Accepts numerical environmental readings via payload or trigger.",
                "pass_condition": "Numerical values for temperature, humidity, and wind speed are parsed and present.",
            },
            {
                "id": "AC2",
                "requirement_id": "FR2",
                "criteria": "System must validate physical bounds for atmospheric parameters.",
                "description": "Enforces humidity in [0, 100]% and wind speed >= 0.",
                "pass_condition": "Out-of-range sensor parameters raise structured validation error.",
            },
            {
                "id": "AC3",
                "requirement_id": "FR3",
                "criteria": "AI reasoning must predict weather conditions and classify precipitation/storm risk.",
                "description": "Uses LLM reasoning to evaluate atmospheric parameters into conditions (e.g., sunny, rainy).",
                "pass_condition": "Prediction output contains condition classification and confidence score.",
            },
            {
                "id": "AC4",
                "requirement_id": "FR4",
                "criteria": "System must produce a structured weather prediction report deliverable.",
                "description": "Delivers complete forecast markdown report containing summary and advisories.",
                "pass_condition": "Output deliverable contains formatted weather prediction report.",
            },
        ]
    elif is_resume:
        return [
            {
                "id": "AC1",
                "requirement_id": "FR1",
                "criteria": "System must extract text and skills from uploaded PDF resumes.",
                "description": "Parses document content and structures candidate capabilities.",
                "pass_condition": "Extracted skills array is non-empty and accurately reflects resume content.",
            },
            {
                "id": "AC2",
                "requirement_id": "FR2",
                "criteria": "System must parse target job description requirements.",
                "description": "Identifies mandatory qualifications, experience levels, and skills.",
                "pass_condition": "Job requirements checklist generated for comparison.",
            },
            {
                "id": "AC3",
                "requirement_id": "FR3",
                "criteria": "AI model must compare candidate skills against job description and compute match score.",
                "description": "Computes semantic alignment, strengths, and missing qualification gaps.",
                "pass_condition": "Fit score (0-10 or 0-100%) and skill match breakdown are computed.",
            },
            {
                "id": "AC4",
                "requirement_id": "FR4",
                "criteria": "System must generate a formatted candidate evaluation report.",
                "description": "Outputs finalized candidate evaluation report with recommendation.",
                "pass_condition": "Structured candidate evaluation report generated.",
            },
        ]
    elif is_invoice:
        return [
            {
                "id": "AC1",
                "requirement_id": "FR1",
                "criteria": "System must parse invoice document text and line item tables.",
                "description": "Extracts totals, taxes, vendor info, and line items.",
                "pass_condition": "Invoice line items and total amounts are structured.",
            },
            {
                "id": "AC2",
                "requirement_id": "FR2",
                "criteria": "System must audit totals against purchase order rules.",
                "description": "Verifies math accuracy and threshold compliance.",
                "pass_condition": "Audit passes or flags discrepancy when totals mismatch.",
            },
            {
                "id": "AC3",
                "requirement_id": "FR3",
                "criteria": "System must produce an invoice audit report.",
                "description": "Outputs audit summary and approval status.",
                "pass_condition": "Final invoice verification deliverable generated.",
            },
        ]
    else:
        return [
            {
                "id": "AC1",
                "requirement_id": "FR1",
                "criteria": f"System must successfully process inputs for '{objective}'.",
                "description": "Validates and parses required input data.",
                "pass_condition": "Input validation passes without unhandled exceptions.",
            },
            {
                "id": "AC2",
                "requirement_id": "FR2",
                "criteria": "AI reasoning module must execute workflow logic adhering to constraints.",
                "description": "Applies cognitive reasoning and task execution.",
                "pass_condition": "LLM response is successfully generated and matches schema.",
            },
            {
                "id": "AC3",
                "requirement_id": "FR3",
                "criteria": "System must generate the designated final output report or deliverable.",
                "description": "Delivers formatted results to the user or downstream sink.",
                "pass_condition": "Final output is produced and non-empty.",
            },
        ]


def _heuristic_edge_cases(
    objective: str,
    requirements: Dict[str, Any],
    description: str,
) -> List[Dict[str, Any]]:
    p_lower = description.lower()
    is_weather = _has_keyword(p_lower, ["weather", "temperature", "humidity", "wind", "forecast", "climate"])
    is_resume = _has_keyword(p_lower, ["resume", "candidate", "applicant", "hire", "recruiting", "cv"])

    if is_weather:
        return [
            {
                "scenario_id": "EC1",
                "description": "Empty or missing weather parameters in input payload",
                "input_condition": "Null, blank, or missing temperature/humidity/wind speed fields",
                "expected_behavior": "Input node catches missing field and raises a clear 400 validation error",
                "expected_result": "Validation error specifying missing weather parameters",
                "severity": "High",
            },
            {
                "scenario_id": "EC2",
                "description": "Physical parameter boundary violation",
                "input_condition": "Humidity < 0% or > 100%, or wind speed < 0 km/h",
                "expected_behavior": "Validation rule flags out-of-bounds sensor reading before invoking LLM",
                "expected_result": "Descriptive range violation message returned safely",
                "severity": "High",
            },
            {
                "scenario_id": "EC3",
                "description": "Severe atmospheric condition or extreme storm metrics",
                "input_condition": "Wind speed > 100 km/h or extreme typhoon/blizzard values",
                "expected_behavior": "Condition node routes to emergency weather advisory branch",
                "expected_result": "Severe weather alert banner prominently included in output report",
                "severity": "Medium",
            },
            {
                "scenario_id": "EC4",
                "description": "LLM API timeout or rate limit exceeded",
                "input_condition": "Upstream AI provider unavailable or response timeout > 10s",
                "expected_behavior": "Fallback to deterministic weather estimation heuristics",
                "expected_result": "Report generated with fallback estimation notice",
                "severity": "Medium",
            },
        ]
    elif is_resume:
        return [
            {
                "scenario_id": "EC1",
                "description": "Empty or corrupt resume file uploaded",
                "input_condition": "0-byte file, unreadable PDF, or password-protected document",
                "expected_behavior": "Document Reader catches read error and returns clean user notice",
                "expected_result": "Validation error: 'Unable to parse document. Please upload an unprotected PDF.'",
                "severity": "High",
            },
            {
                "scenario_id": "EC2",
                "description": "Missing job description context",
                "input_condition": "Candidate resume provided without job description or role requirements",
                "expected_behavior": "System flags missing benchmark and requests job description",
                "expected_result": "Clarification required or default generic skills profile generated",
                "severity": "Medium",
            },
            {
                "scenario_id": "EC3",
                "description": "Low qualification match below passing threshold",
                "input_condition": "Candidate skills have 0% overlap with mandatory criteria",
                "expected_behavior": "Condition node routes to rejection notice rather than human interview review",
                "expected_result": "Evaluation report highlights significant skill gap with 'Not Recommended' status",
                "severity": "Low",
            },
            {
                "scenario_id": "EC4",
                "description": "LLM API timeout or rate limit exceeded",
                "input_condition": "Upstream Gemini model rate limit or connection timeout",
                "expected_behavior": "Retry with exponential backoff; fallback to deterministic keyword matcher",
                "expected_result": "Report synthesized using deterministic fallback engine",
                "severity": "Medium",
            },
        ]
    else:
        return [
            {
                "scenario_id": "EC1",
                "description": "Missing or null input parameters",
                "input_condition": "Empty request body or required keys missing",
                "expected_behavior": "Input component validates schema and returns informative error",
                "expected_result": "Descriptive 422/400 validation error response",
                "severity": "High",
            },
            {
                "scenario_id": "EC2",
                "description": "Malformed or out-of-range input values",
                "input_condition": "Unexpected data types, non-numeric values, or corrupt attachments",
                "expected_behavior": "Input parser safely halts execution before downstream components",
                "expected_result": "Schema format violation error logged and returned",
                "severity": "High",
            },
            {
                "scenario_id": "EC3",
                "description": "LLM service degradation or network timeout",
                "input_condition": "AI provider service outage, rate limiting, or socket timeout",
                "expected_behavior": "Execute retry policy with backoff; fall back to deterministic pipeline",
                "expected_result": "Workflow completes with fallback indicator or clear degradation notice",
                "severity": "Medium",
            },
        ]


def _heuristic_test_scenarios(
    objective: str,
    requirements: Dict[str, Any],
    tasks: List[Dict[str, Any]],
    description: str,
) -> List[Dict[str, Any]]:
    p_lower = description.lower()
    is_weather = _has_keyword(p_lower, ["weather", "temperature", "humidity", "wind", "forecast", "climate"])
    is_resume = _has_keyword(p_lower, ["resume", "candidate", "applicant", "hire", "recruiting", "cv"])

    if is_weather:
        return [
            {
                "test_id": "TS1",
                "requirement_id": "AC1",
                "test_description": "Verify nominal weather prediction pipeline with valid inputs",
                "test_input": {"temperature": 22.5, "humidity": 60, "wind_speed": 15.0},
                "expected_output": "Weather prediction report containing condition classification and summary",
                "expected_status": "SUCCESS",
                "pass_fail_condition": "Status is SUCCESS and output report is non-empty with condition predicted",
                "scenario_type": "positive",
            },
            {
                "test_id": "TS2",
                "requirement_id": "AC2",
                "test_description": "Verify rejection of empty input payload",
                "test_input": {},
                "expected_output": "Validation error indicating missing required weather fields",
                "expected_status": "FAILURE",
                "pass_fail_condition": "Execution halts at Input node with descriptive validation error",
                "scenario_type": "negative",
            },
            {
                "test_id": "TS3",
                "requirement_id": "AC2",
                "test_description": "Verify boundary validation for out-of-bounds humidity and wind speed",
                "test_input": {"temperature": 25.0, "humidity": 150, "wind_speed": -10.0},
                "expected_output": "Boundary range validation error",
                "expected_status": "FAILURE",
                "pass_fail_condition": "System catches out-of-range sensor readings without unhandled exceptions",
                "scenario_type": "negative",
            },
            {
                "test_id": "TS4",
                "requirement_id": "AC3",
                "test_description": "Verify severe storm alert triggering when wind speed exceeds threshold",
                "test_input": {"temperature": 18.0, "humidity": 95, "wind_speed": 75.0},
                "expected_output": "Weather prediction report with high-wind severe weather warning advisory",
                "expected_status": "SUCCESS",
                "pass_fail_condition": "Condition node routes to severe alert and report includes advisory banner",
                "scenario_type": "edge_case",
            },
        ]
    elif is_resume:
        return [
            {
                "test_id": "TS1",
                "requirement_id": "AC1",
                "test_description": "Verify candidate evaluation with valid resume and job description",
                "test_input": {
                    "resume_url": "https://agentforge.ai/samples/john_doe_resume.pdf",
                    "job_description": "Looking for Senior Python Developer with FastAPI and AI experience.",
                },
                "expected_output": "Candidate evaluation report with match score and skill breakdown",
                "expected_status": "SUCCESS",
                "pass_fail_condition": "Evaluation report generated with positive match score",
                "scenario_type": "positive",
            },
            {
                "test_id": "TS2",
                "requirement_id": "AC2",
                "test_description": "Verify failure when no resume document is provided",
                "test_input": {"job_description": "Senior Python Developer"},
                "expected_output": "Validation error for missing resume document",
                "expected_status": "FAILURE",
                "pass_fail_condition": "Input validation halts execution with missing document error",
                "scenario_type": "negative",
            },
            {
                "test_id": "TS3",
                "requirement_id": "AC3",
                "test_description": "Verify low qualification score routing when skills completely mismatch",
                "test_input": {
                    "resume_url": "https://agentforge.ai/samples/chef_resume.pdf",
                    "job_description": "Quantum Computing Physicist with Qiskit expertise.",
                },
                "expected_output": "Evaluation report with low suitability score and non-recommended status",
                "expected_status": "SUCCESS",
                "pass_fail_condition": "Fit score < 3.0 and report explicitly notes qualification mismatch",
                "scenario_type": "edge_case",
            },
        ]
    else:
        return [
            {
                "test_id": "TS1",
                "requirement_id": "AC1",
                "test_description": "Verify successful end-to-end workflow execution with valid inputs",
                "test_input": {"query": description},
                "expected_output": "Workflow output deliverable successfully produced",
                "expected_status": "SUCCESS",
                "pass_fail_condition": "All tasks in execution plan complete and deliverable is produced",
                "scenario_type": "positive",
            },
            {
                "test_id": "TS2",
                "requirement_id": "AC1",
                "test_description": "Verify rejection of empty or missing mandatory inputs",
                "test_input": {},
                "expected_output": "Validation error response",
                "expected_status": "FAILURE",
                "pass_fail_condition": "System returns input validation error rather than crashing",
                "scenario_type": "negative",
            },
        ]


def _heuristic_assumptions(
    objective: str,
    requirements: Dict[str, Any],
    description: str,
) -> List[str]:
    return [
        "User input parameters conform to specified JSON or file schemas.",
        "Google Gemini API or local deterministic engine is accessible during execution.",
        "Member 3 runtime strictly implements the 7 canonical workflow components (Input, LLM, Document Reader, Tool, Condition, Human Approval, Output).",
        "Automated verification will be conducted by Member 5 test harness using generated test scenarios.",
    ]


def _heuristic_task_decomposition(
    objective: str,
    requirements: Dict[str, Any],
    description: str,
) -> List[Dict[str, Any]]:
    """Generates ordered executable tasks with dependencies and components."""
    p_lower = description.lower()
    tasks: List[Dict[str, Any]] = []

    is_weather = any(w in p_lower for w in ["weather", "temperature", "humidity", "wind", "forecast", "climate"])
    if is_weather:
        return [
            {
                "task_id": "T1",
                "task_name": "Ingest Weather Data",
                "description": "Ingest environmental metrics: temperature, humidity, and wind speed readings.",
                "task_description": "Ingest environmental metrics: temperature, humidity, and wind speed readings.",
                "component": "Input",
                "component_type": "Input",
                "required_component": "Input",
                "input": "User payload: temperature, humidity, wind speed",
                "expected_output": "Validated atmospheric metric payload",
                "dependencies": [],
                "execution_order": 1,
                "component_config_hints": {"parameters": ["temperature", "humidity", "wind_speed"], "format": "json"}
            },
            {
                "task_id": "T2",
                "task_name": "Predict Weather Conditions",
                "description": "Analyze environmental metrics using Gemini AI reasoning to predict conditions and precipitation risk.",
                "task_description": "Analyze environmental metrics using Gemini AI reasoning to predict conditions and precipitation risk.",
                "component": "LLM",
                "component_type": "LLM",
                "required_component": "LLM",
                "input": "Validated metrics from T1",
                "expected_output": "Predicted weather conditions, forecast summary, and risk classifications",
                "dependencies": ["T1"],
                "execution_order": 2,
                "component_config_hints": {"model": "gemini-1.5-pro", "temperature": 0.2}
            },
            {
                "task_id": "T3",
                "task_name": "Check Severe Weather Alert",
                "description": "Evaluate threshold rules (high wind speed or severe conditions) to determine hazard warnings.",
                "task_description": "Evaluate threshold rules (high wind speed or severe conditions) to determine hazard warnings.",
                "component": "Condition",
                "component_type": "Condition",
                "required_component": "Condition",
                "input": "Weather condition metrics from T2",
                "expected_output": "Severe weather alert routing flag",
                "dependencies": ["T2"],
                "execution_order": 3,
                "component_config_hints": {"rule": "wind_speed > 50 or condition == 'severe'"}
            },
            {
                "task_id": "T4",
                "task_name": "Generate Weather Prediction Report",
                "description": "Synthesize and format final weather prediction report with forecast and advisories.",
                "task_description": "Synthesize and format final weather prediction report with forecast and advisories.",
                "component": "Output",
                "component_type": "Output",
                "required_component": "Output",
                "input": "Forecast analysis and alert details from T3",
                "expected_output": "Formatted comprehensive weather prediction report",
                "dependencies": ["T3"],
                "execution_order": 4,
                "component_config_hints": {"format": "markdown_report"}
            }
        ]

    is_resume = _has_keyword(p_lower, ["resume", "candidate", "applicant", "hire", "cv"])
    is_invoice = _has_keyword(p_lower, ["invoice", "receipt", "bill", "vendor", "po", "purchase order"])
    has_doc = _has_keyword(p_lower, ["pdf", "resume", "invoice", "doc", "document", "file", "cv", "receipt", "manual"])
    needs_condition = any(w in p_lower for w in ["condition", "threshold", "score", "if", "check"])
    needs_approval = any(w in p_lower for w in ["approval", "human", "review", "signoff", "manager"])
    needs_tool = any(w in p_lower for w in ["slack", "email", "database", "save", "erp", "sync", "api"])

    order = 1
    # 1. Input Task
    t1_id = f"T{order}"
    tasks.append({
        "task_id": t1_id,
        "task_name": "Upload Resume" if is_resume else "Upload Input Data",
        "description": "Ingest user-provided source files or parameters.",
        "task_description": "Ingest user-provided source files or parameters.",
        "component": "Input",
        "component_type": "Input",
        "required_component": "Input",
        "input": "User upload trigger / files",
        "expected_output": "Raw uploaded file references",
        "dependencies": [],
        "execution_order": order,
        "component_config_hints": {"inputType": "file_url" if has_doc else "text", "required": True}
    })
    prev_id = t1_id
    order += 1

    # 2. Document Reader Task (if documents involved)
    if has_doc or is_resume or is_invoice:
        t2_id = f"T{order}"
        tasks.append({
            "task_id": t2_id,
            "task_name": "Extract Resume Data" if is_resume else "Extract Document Data",
            "description": "Parse text, tables, and metadata from incoming files.",
            "task_description": "Parse text, tables, and metadata from incoming files.",
            "component": "Document Reader",
            "component_type": "Document Reader",
            "required_component": "Document Reader",
            "input": f"File from {prev_id}",
            "expected_output": "Parsed text and structured entity chunks",
            "dependencies": [prev_id],
            "execution_order": order,
            "component_config_hints": {"supportedExtensions": [".pdf", ".docx"], "extractTables": True}
        })
        prev_id = t2_id
        order += 1

    # 3. LLM Reasoning / Extraction Task
    t3_id = f"T{order}"
    llm_name = "Analyze and Compare Skills" if is_resume else ("Extract & Audit Line Items" if is_invoice else "Analyze and Process Context")
    tasks.append({
        "task_id": t3_id,
        "task_name": llm_name,
        "description": "Apply Gemini LLM reasoning to evaluate context against target criteria.",
        "task_description": "Apply Gemini LLM reasoning to evaluate context against target criteria.",
        "component": "LLM",
        "component_type": "LLM",
        "required_component": "LLM",
        "input": f"Extracted data from {prev_id}",
        "expected_output": "Structured analysis, scores, and evaluation insights",
        "dependencies": [prev_id],
        "execution_order": order,
        "component_config_hints": {"model": "gemini-1.5-pro", "temperature": 0.3}
    })
    prev_id = t3_id
    order += 1

    # 4. Optional Condition Task
    if needs_condition or is_resume or is_invoice:
        t_cond_id = f"T{order}"
        tasks.append({
            "task_id": t_cond_id,
            "task_name": "Check Evaluation Threshold",
            "description": "Evaluate conditional rule against scores to determine next pathway.",
            "task_description": "Evaluate conditional rule against scores to determine next pathway.",
            "component": "Condition",
            "component_type": "Condition",
            "required_component": "Condition",
            "input": f"Score from {prev_id}",
            "expected_output": "Boolean branching decision (true/false)",
            "dependencies": [prev_id],
            "execution_order": order,
            "component_config_hints": {"rule": "fit_score >= 7.0"}
        })
        prev_id = t_cond_id
        order += 1

    # 5. Optional Human Approval Task
    if needs_approval or is_resume:
        t_app_id = f"T{order}"
        tasks.append({
            "task_id": t_app_id,
            "task_name": "Review Decision",
            "description": "Human-in-the-loop checkpoint for manual verification.",
            "task_description": "Human-in-the-loop checkpoint for manual verification.",
            "component": "Human Approval",
            "component_type": "Human Approval",
            "required_component": "Human Approval",
            "input": f"Decision data from {prev_id}",
            "expected_output": "Human approval confirmation or rejection",
            "dependencies": [prev_id],
            "execution_order": order,
            "component_config_hints": {"approverRole": "Manager", "timeoutHours": 24}
        })
        prev_id = t_app_id
        order += 1

    # 6. Optional Tool Task
    if needs_tool:
        t_tool_id = f"T{order}"
        tasks.append({
            "task_id": t_tool_id,
            "task_name": "Dispatch External Notification / Sync",
            "description": "Execute external API call, database record creation, or notification.",
            "task_description": "Execute external API call, database record creation, or notification.",
            "component": "Tool",
            "component_type": "Tool",
            "required_component": "Tool",
            "input": f"Data from {prev_id}",
            "expected_output": "External sync response status",
            "dependencies": [prev_id],
            "execution_order": order,
            "component_config_hints": {"toolAction": "sync_record"}
        })
        prev_id = t_tool_id
        order += 1

    # 7. Final Output Task
    t_out_id = f"T{order}"
    tasks.append({
        "task_id": t_out_id,
        "task_name": "Generate Evaluation Report" if is_resume else "Generate Final Output",
        "description": "Format and deliver the final output report or payload.",
        "task_description": "Format and deliver the final output report or payload.",
        "component": "Output",
        "component_type": "Output",
        "required_component": "Output",
        "input": f"Synthesized outputs from {prev_id}",
        "expected_output": "Formatted final deliverable",
        "dependencies": [prev_id],
        "execution_order": order,
        "component_config_hints": {"format": "markdown_report"}
    })

    return tasks


# ---------------------------------------------------------------------------
# LangGraph Nodes Implementation
# ---------------------------------------------------------------------------

def requirement_input_node(state: RequirementAnalysisState) -> RequirementAnalysisState:
    """
    Node 1: Requirement Input Node.
    Receives user description and any existing clarification answers.
    Normalizes input and initializes the state graph.
    """
    description = (state.get("description") or "").strip()
    clarification_answers = state.get("clarification_answers") or {}
    context = state.get("context") or {}

    logger.info(f"[LangGraph:Node 1] Requirement Input: '{description[:60]}...' (Answers: {len(clarification_answers)})")

    return {
        "description": description,
        "clarification_answers": clarification_answers,
        "context": context,
        "errors": [],
        "validation_notes": [],
    }


def requirement_analysis_node(state: RequirementAnalysisState) -> RequirementAnalysisState:
    """
    Node 2: Requirement Analysis Node.
    Understands the objective, identifies the problem, expected outputs,
    and extracts structured requirements.
    Uses Google Gemini API when available, with intelligent fallback.
    """
    description = state.get("description", "")
    clarification_answers = state.get("clarification_answers", {})

    logger.info("[LangGraph:Node 2] Requirement Analysis Node executing...")

    prompt = f"""
You are an expert AI Architect. Analyze this user instruction to build an autonomous agent workflow:

User Description:
"{description}"

Clarification Answers Provided by User:
{json.dumps(clarification_answers, indent=2)}

Extract the following in structured JSON:
{{
  "project_objective": "Concise high-level objective of what this agent accomplishes",
  "inputs": ["List of input requirements e.g. PDF resume, Job description"],
  "processing": ["List of sequential processing requirements"],
  "outputs": ["List of expected final outputs"],
  "tools": ["List of required external tools if any, e.g. Email, Slack, DB"],
  "constraints": ["List of execution constraints e.g. threshold rules, human sign-off"],
  "functional": ["List of functional capabilities and operations"],
  "non_functional": ["List of non-functional requirements e.g. latency, safety, resilience"]
}}
"""
    system_instruction = (
        "You are the AgentForge AI Requirement Analysis Engine. Deconstruct natural language "
        "instructions into rigorous, structured requirements. Output ONLY valid JSON."
    )

    gemini_data = call_gemini_json(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=0.2,
    )

    if gemini_data and isinstance(gemini_data, dict) and "project_objective" in gemini_data:
        logger.info("[LangGraph:Node 2] Successfully extracted requirements via Gemini API.")
        project_objective = gemini_data.get("project_objective", "")
        requirements = {
            "inputs": gemini_data.get("inputs", []),
            "processing": gemini_data.get("processing", []),
            "outputs": gemini_data.get("outputs", []),
            "tools": gemini_data.get("tools", []),
            "constraints": gemini_data.get("constraints", []),
            "functional": gemini_data.get("functional", gemini_data.get("processing", [])),
            "non_functional": gemini_data.get("non_functional", ["Workflow execution follows topological dependency order"]),
        }
        ai_provider = "google-gemini"
        model_used = getattr(settings, "GEMINI_DEFAULT_MODEL", "gemini-1.5-pro")
    else:
        logger.info("[LangGraph:Node 2] Using resilient semantic fallback for requirement analysis.")
        fallback = _heuristic_requirement_analysis(description, clarification_answers)
        project_objective = fallback["project_objective"]
        requirements = {
            "inputs": fallback["inputs"],
            "processing": fallback["processing"],
            "outputs": fallback["outputs"],
            "tools": fallback["tools"],
            "constraints": fallback["constraints"],
            "functional": fallback.get("functional", []),
            "non_functional": fallback.get("non_functional", []),
        }
        ai_provider = "deterministic_engine"
        model_used = None

    return {
        "project_objective": project_objective,
        "requirements": requirements,
        "ai_provider": ai_provider,
        "model_used": model_used,
    }


def task_decomposition_node(state: RequirementAnalysisState) -> RequirementAnalysisState:
    """
    Node 3: Task Decomposition Node.
    Breaks requirements into ordered, discrete, executable tasks with:
    Task ID, Task Name, Task Description, Input, Expected Output, Dependencies, Execution Order.
    """
    logger.info("[LangGraph:Node 3] Task Decomposition Node executing...")

    objective = state.get("project_objective", "")
    requirements = state.get("requirements", {})
    description = state.get("description", "")

    # Ask Gemini for decomposition if available
    prompt = f"""
Given the project objective and requirements:
Objective: "{objective}"
Requirements: {json.dumps(requirements)}
Original Description: "{description}"

Decompose into an ordered sequence of executable tasks.
Supported components strictly allowed: "Input", "LLM", "Document Reader", "Tool", "Condition", "Human Approval", "Output".
Do NOT use any other component names.

Respond with JSON:
{{
  "tasks": [
    {{
      "task_id": "T1",
      "task_name": "Upload Resume",
      "task_description": "Ingest user resume file",
      "description": "Ingest user resume file",
      "component": "Input",
      "component_type": "Input",
      "input": "User upload",
      "expected_output": "Resume file",
      "dependencies": [],
      "execution_order": 1,
      "component_config_hints": {{}}
    }}
  ]
}}
"""
    gemini_data = call_gemini_json(prompt=prompt, temperature=0.2)
    raw_tasks = []
    if gemini_data and isinstance(gemini_data, dict) and "tasks" in gemini_data:
        raw_tasks = gemini_data.get("tasks", [])

    if not raw_tasks or not isinstance(raw_tasks, list) or len(raw_tasks) < 2:
        raw_tasks = _heuristic_task_decomposition(objective, requirements, description)

    return {
        "tasks": raw_tasks,
    }


def component_selection_node(state: RequirementAnalysisState) -> RequirementAnalysisState:
    """
    Node 4: Component Selection Node.
    Identifies which of the 7 supported components are required:
    1. Input
    2. LLM
    3. Document Reader
    4. Tool
    5. Condition
    6. Human Approval
    7. Output
    Strictly validates and maps task components without inventing unsupported types.
    """
    logger.info("[LangGraph:Node 4] Component Selection Node executing...")

    tasks = state.get("tasks", [])
    selected_components_set = set()
    sanitized_tasks: List[Dict[str, Any]] = []

    # Mapping dictionary for common variations to canonical components
    normalization_map = {
        "input": "Input",
        "fileinput": "Input",
        "prompt": "Input",
        "user_input": "Input",
        "llm": "LLM",
        "ai": "LLM",
        "model": "LLM",
        "assistant": "LLM",
        "gemini": "LLM",
        "document reader": "Document Reader",
        "documentreader": "Document Reader",
        "reader": "Document Reader",
        "pdf_reader": "Document Reader",
        "parser": "Document Reader",
        "tool": "Tool",
        "api": "Tool",
        "database": "Tool",
        "db": "Tool",
        "slack": "Tool",
        "condition": "Condition",
        "branch": "Condition",
        "decision": "Condition",
        "human approval": "Human Approval",
        "humanapproval": "Human Approval",
        "human_approval": "Human Approval",
        "approval": "Human Approval",
        "review": "Human Approval",
        "output": "Output",
        "sink": "Output",
        "report": "Output",
        "export": "Output",
    }

    for task in tasks:
        raw_comp = str(
            task.get("component") or
            task.get("component_type") or
            task.get("required_component") or
            "LLM"
        ).strip()
        comp_lower = raw_comp.lower()

        # Normalize to canonical 7
        matched_comp = normalization_map.get(comp_lower)
        if not matched_comp:
            for canonical in SUPPORTED_COMPONENTS_LIST:
                if canonical.lower() in comp_lower or comp_lower in canonical.lower():
                    matched_comp = canonical
                    break

        canonical_comp: SupportedComponent = matched_comp or "LLM"
        selected_components_set.add(canonical_comp)

        sanitized_task = dict(task)
        sanitized_task["component"] = canonical_comp
        sanitized_task["component_type"] = canonical_comp
        sanitized_task["required_component"] = canonical_comp
        if not sanitized_task.get("description") and sanitized_task.get("task_description"):
            sanitized_task["description"] = sanitized_task["task_description"]
        sanitized_tasks.append(sanitized_task)

    # Order required_components according to canonical order
    required_components = [c for c in SUPPORTED_COMPONENTS_LIST if c in selected_components_set]

    return {
        "tasks": sanitized_tasks,
        "selected_components": required_components,
    }


def requirement_validation_node(state: RequirementAnalysisState) -> RequirementAnalysisState:
    """
    Node 5: Requirement Validation Node.
    Detects missing or ambiguous requirements.
    If important information is missing and no clarification answers provided:
    - Generates relevant clarification questions
    - Explains why clarification is needed
    - Sets is_valid = False, status = "needs_clarification"
    Otherwise sets is_valid = True, status = "ready".
    """
    logger.info("[LangGraph:Node 5] Requirement Validation Node executing...")

    description = state.get("description", "")
    clarification_answers = state.get("clarification_answers", {})
    requirements = state.get("requirements", {})

    # Detect missing requirements
    clarification_questions = _detect_missing_and_clarifications(
        description,
        clarification_answers,
        extracted_requirements=requirements,
    )

    # If critical information is missing and questions remain unanswered
    if clarification_questions:
        logger.info(f"[LangGraph:Node 5] Missing info detected. Generated {len(clarification_questions)} clarification questions.")
        return {
            "is_valid": False,
            "status": "needs_clarification",
            "clarification_questions": clarification_questions,
            "confidence_score": 0.55,
            "validation_notes": ["Missing input or output specifications require user clarification before planning."],
        }

    logger.info("[LangGraph:Node 5] Validation passed. Requirements are clear and complete.")
    return {
        "is_valid": True,
        "status": "ready",
        "clarification_questions": [],
        "confidence_score": 0.95,
        "validation_notes": ["Requirements complete, verified against canonical component model."],
    }


def route_after_validation(state: RequirementAnalysisState) -> str:
    """Conditional routing edge: routes to planning if valid, or output if clarification needed."""
    if state.get("is_valid", False):
        return "planning"
    return "output"


def planning_node(state: RequirementAnalysisState) -> RequirementAnalysisState:
    """
    Node 6: Planning Node.
    Synthesizes requirements, ordered tasks, component hints, acceptance criteria,
    edge cases, and test scenarios into the structured execution plan.
    """
    logger.info("[LangGraph:Node 6] Planning Node generating structured execution plan...")

    tasks = state.get("tasks", [])
    objective = state.get("project_objective", "Custom AI Agent Workflow")
    selected_components = state.get("selected_components", [])
    description = state.get("description", "")
    requirements = state.get("requirements", {})

    # Re-sequence execution order cleanly 1..N
    ordered_tasks = []
    for idx, t in enumerate(tasks, start=1):
        task_item = dict(t)
        task_item["execution_order"] = idx
        ordered_tasks.append(task_item)

    architecture_summary = (
        f"Execution plan for '{objective}' with {len(ordered_tasks)} ordered tasks "
        f"utilizing components: {', '.join(selected_components)}."
    )

    # Synthesize Acceptance Criteria if not already provided
    acceptance_criteria = state.get("acceptance_criteria")
    if not acceptance_criteria:
        acceptance_criteria = _heuristic_acceptance_criteria(objective, requirements, description)

    # Synthesize Edge Cases if not already provided
    edge_cases = state.get("edge_cases")
    if not edge_cases:
        edge_cases = _heuristic_edge_cases(objective, requirements, description)

    # Synthesize Test Scenarios if not already provided
    test_scenarios = state.get("test_scenarios")
    if not test_scenarios:
        test_scenarios = _heuristic_test_scenarios(objective, requirements, ordered_tasks, description)

    # Synthesize Assumptions
    assumptions = state.get("assumptions")
    if not assumptions:
        assumptions = _heuristic_assumptions(objective, requirements, description)

    return {
        "tasks": ordered_tasks,
        "architecture_summary": architecture_summary,
        "acceptance_criteria": acceptance_criteria,
        "edge_cases": edge_cases,
        "test_scenarios": test_scenarios,
        "assumptions": assumptions,
        "status": "ready",
    }


def output_node(state: RequirementAnalysisState) -> RequirementAnalysisState:
    """
    Node 7: Output Node.
    Assembles the final structured ExecutionPlanResponse ready for Member 3 and Member 5.
    """
    logger.info("[LangGraph:Node 7] Output Node packaging final response.")

    objective = state.get("project_objective", "Custom AI Agent Workflow")
    status = state.get("status", "ready")
    req_dict = state.get("requirements", {})

    requirements = RequirementsBreakdown(
        inputs=req_dict.get("inputs", []),
        processing=req_dict.get("processing", []),
        outputs=req_dict.get("outputs", []),
        expected_outputs=req_dict.get("outputs", []),
        tools=req_dict.get("tools", []),
        constraints=req_dict.get("constraints", []),
        functional=req_dict.get("functional", []),
        non_functional=req_dict.get("non_functional", []),
    )

    tasks_out = []
    for t in state.get("tasks", []):
        try:
            tasks_out.append(TaskDecompositionItem(**t))
        except Exception as e:
            logger.warning(f"Failed to validate task item {t}: {e}")

    clarification_questions = [
        ClarificationQuestion(**q) for q in state.get("clarification_questions", [])
    ]

    # Acceptance criteria
    acceptance_criteria_out = []
    for ac in state.get("acceptance_criteria", []):
        try:
            acceptance_criteria_out.append(AcceptanceCriterion(**ac))
        except Exception as e:
            logger.warning(f"Failed to validate acceptance criterion {ac}: {e}")

    # Edge cases
    edge_cases_out = []
    for ec in state.get("edge_cases", []):
        try:
            edge_cases_out.append(EdgeCaseScenario(**ec))
        except Exception as e:
            logger.warning(f"Failed to validate edge case {ec}: {e}")

    # Test scenarios
    test_scenarios_out = []
    for ts in state.get("test_scenarios", []):
        try:
            test_scenarios_out.append(TestScenario(**ts))
        except Exception as e:
            logger.warning(f"Failed to validate test scenario {ts}: {e}")

    assumptions_out = state.get("assumptions", [])

    selected_comps = state.get("selected_components", [])
    valid_comps: List[SupportedComponent] = [
        c for c in selected_comps if c in SUPPORTED_COMPONENTS_LIST
    ]

    final_response = ExecutionPlanResponse(
        project_objective=objective,
        status=status,
        requirements=requirements,
        tasks=tasks_out,
        execution_plan=tasks_out,
        required_components=valid_comps,
        components=valid_comps,
        clarification_questions=clarification_questions,
        acceptance_criteria=acceptance_criteria_out,
        edge_cases=edge_cases_out,
        test_scenarios=test_scenarios_out,
        assumptions=assumptions_out,
        confidence_score=state.get("confidence_score", 0.95),
        architecture_summary=state.get("architecture_summary"),
        ai_provider=state.get("ai_provider", "deterministic_engine"),
        model_used=state.get("model_used"),
        contract_version="1.1.0",
    )

    return {
        "final_plan": final_response.model_dump(),
    }


# ---------------------------------------------------------------------------
# LangGraph Workflow Construction
# ---------------------------------------------------------------------------

def build_requirement_analysis_graph():
    """Builds and compiles the 7-node LangGraph StateGraph with conditional routing."""
    workflow = StateGraph(RequirementAnalysisState)

    # 1. Add 7 Nodes
    workflow.add_node("requirement_input", requirement_input_node)
    workflow.add_node("requirement_analysis", requirement_analysis_node)
    workflow.add_node("task_decomposition", task_decomposition_node)
    workflow.add_node("component_selection", component_selection_node)
    workflow.add_node("requirement_validation", requirement_validation_node)
    workflow.add_node("planning", planning_node)
    workflow.add_node("output", output_node)

    # 2. Sequential Edges
    workflow.add_edge(START, "requirement_input")
    workflow.add_edge("requirement_input", "requirement_analysis")
    workflow.add_edge("requirement_analysis", "task_decomposition")
    workflow.add_edge("task_decomposition", "component_selection")
    workflow.add_edge("component_selection", "requirement_validation")

    # 3. Conditional Routing from Validation
    workflow.add_conditional_edges(
        "requirement_validation",
        route_after_validation,
        {
            "planning": "planning",
            "output": "output",
        },
    )

    # 4. Terminal Edges
    workflow.add_edge("planning", "output")
    workflow.add_edge("output", END)

    return workflow.compile()


# Compiled Singleton Graph
requirement_graph = build_requirement_analysis_graph()


class RequirementAnalysisService:
    """Service wrapping the LangGraph AI Planning Workflow for Member 2."""

    def __init__(self):
        self.graph = requirement_graph

    def analyze_requirements(
        self,
        description: str,
        clarification_answers: Optional[Dict[str, str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlanResponse:
        """
        Executes the LangGraph AI requirement analysis workflow.
        Returns a validated ExecutionPlanResponse compatible with Member 3.
        """
        initial_state: RequirementAnalysisState = {
            "description": description,
            "clarification_answers": clarification_answers or {},
            "context": context or {},
        }

        result = self.graph.invoke(initial_state)
        final_dict = result.get("final_plan") or {}

        return ExecutionPlanResponse(**final_dict)
