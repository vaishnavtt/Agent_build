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
    requirements: Dict[str, Any]  # inputs, processing, outputs, tools, constraints
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

    # Detect domain
    is_resume = any(w in p_lower for w in ["resume", "candidate", "job", "applicant", "hire", "recruiting", "cv"])
    is_invoice = any(w in p_lower for w in ["invoice", "receipt", "bill", "vendor", "po", "purchase", "audit"])
    is_qa = any(w in p_lower for w in ["question", "answer", "q&a", "ask", "search doc", "manual"])
    is_summary = any(w in p_lower for w in ["summar", "bullet", "digest", "brief"])

    # Inputs
    inputs = []
    if is_resume:
        inputs = ["PDF resume", "Job description"]
    elif is_invoice:
        inputs = ["Invoice PDF / Image", "Purchase Order specifications"]
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
    if is_resume:
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
    if is_resume:
        outputs = ["Candidate evaluation report"]
    elif is_invoice:
        outputs = ["Verified invoice record and approval status"]
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
    if "score" in p_lower or "threshold" in p_lower:
        constraints.append("Apply pass/fail threshold evaluation")
    if "approval" in p_lower or "human" in p_lower:
        constraints.append("Require human manager sign-off")
    if not constraints:
        constraints.append("Ensure schema adherence and execution safety")

    # Objective
    if is_resume:
        objective = "Evaluate candidates using resumes and job descriptions"
    elif is_invoice:
        objective = "Extract, validate, and process invoice data against compliance rules"
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
    }


def _heuristic_task_decomposition(
    objective: str,
    requirements: Dict[str, Any],
    description: str,
) -> List[Dict[str, Any]]:
    """Generates ordered executable tasks with dependencies and components."""
    p_lower = description.lower()
    tasks: List[Dict[str, Any]] = []

    is_resume = "resume" in p_lower or "candidate" in p_lower or "cv" in p_lower
    is_invoice = "invoice" in p_lower or "receipt" in p_lower or "bill" in p_lower
    has_doc = any(w in p_lower for w in ["pdf", "resume", "invoice", "doc", "file", "cv", "receipt"])
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
  "constraints": ["List of execution constraints e.g. threshold rules, human sign-off"]
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
    Synthesizes requirements, ordered tasks, and component hints into the final
    structured execution plan formatted for Member 3.
    """
    logger.info("[LangGraph:Node 6] Planning Node generating structured execution plan...")

    tasks = state.get("tasks", [])
    objective = state.get("project_objective", "Custom AI Agent Workflow")
    selected_components = state.get("selected_components", [])

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

    return {
        "tasks": ordered_tasks,
        "architecture_summary": architecture_summary,
        "status": "ready",
    }


def output_node(state: RequirementAnalysisState) -> RequirementAnalysisState:
    """
    Node 7: Output Node.
    Assembles the final structured ExecutionPlanResponse ready for Member 3.
    """
    logger.info("[LangGraph:Node 7] Output Node packaging final response.")

    objective = state.get("project_objective", "Custom AI Agent Workflow")
    status = state.get("status", "ready")
    req_dict = state.get("requirements", {})

    requirements = RequirementsBreakdown(
        inputs=req_dict.get("inputs", []),
        processing=req_dict.get("processing", []),
        outputs=req_dict.get("outputs", []),
        tools=req_dict.get("tools", []),
        constraints=req_dict.get("constraints", []),
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

    selected_comps = state.get("selected_components", [])
    valid_comps: List[SupportedComponent] = [
        c for c in selected_comps if c in SUPPORTED_COMPONENTS_LIST
    ]

    final_response = ExecutionPlanResponse(
        project_objective=objective,
        status=status,
        requirements=requirements,
        tasks=tasks_out,
        required_components=valid_comps,
        clarification_questions=clarification_questions,
        confidence_score=state.get("confidence_score", 0.95),
        architecture_summary=state.get("architecture_summary"),
        ai_provider=state.get("ai_provider", "deterministic_engine"),
        model_used=state.get("model_used"),
        contract_version="1.0.0",
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
