"""Agents API Endpoints - Direct management, communication, and execution of the 6 specialized AI agents:
1. Planner Agent
2. Research Agent
3. Execution Agent
4. Validation Agent
5. Error Detection Agent
6. Self-Repair Agent
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.agents.planner_agent import PlannerAgent
from app.agents.research_agent import ResearchAgent
from app.agents.execution_agent import ExecutionAgent
from app.agents.validation_agent import ValidationAgent
from app.agents.error_detection_agent import ErrorDetectionAgent
from app.agents.self_repair_agent import SelfRepairAgent

router = APIRouter()


class AgentInfo(BaseModel):
    id: str
    name: str
    role: str
    status: str = "active"
    description: str
    capabilities: List[str]


class PlanRequest(BaseModel):
    prompt: str = Field(..., min_length=3)
    requirements: Optional[List[str]] = None


class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    context: Optional[Dict[str, Any]] = None


class DiagnoseRequest(BaseModel):
    workflow: Dict[str, Any]
    execution_steps: List[Dict[str, Any]] = Field(default_factory=list)
    error_message: Optional[str] = None


class RepairRequest(BaseModel):
    workflow: Dict[str, Any]
    diagnosis: Dict[str, Any]
    attempt: int = 1


@router.get(
    "",
    response_model=List[AgentInfo],
    summary="List Specialized AI Agents",
    description="Lists the 6 active AI agents, their responsibilities, and operational statuses.",
)
def list_agents() -> List[AgentInfo]:
    return [
        AgentInfo(
            id="planner-agent",
            name="Planner Agent",
            role="Workflow Planner",
            description="Decomposes high-level instructions into multi-agent visual workflows.",
            capabilities=["Requirement deconstruction", "Topology planning", "Node mapping", "Gemini AI generation"],
        ),
        AgentInfo(
            id="research-agent",
            name="Research Agent",
            role="Information Researcher",
            description="Extracts data from documents and prepares domain context for tasks.",
            capabilities=["Document parsing", "Entity extraction", "Context enrichment", "Domain research"],
        ),
        AgentInfo(
            id="execution-agent",
            name="Execution Agent",
            role="Workflow Executor",
            description="Coordinates and executes assigned workflow steps, calling LLMs and tools.",
            capabilities=["Step orchestration", "Gemini LLM reasoning", "Tool invocation", "State tracking"],
        ),
        AgentInfo(
            id="validation-agent",
            name="Validation Agent",
            role="Workflow Validator",
            description="Checks graph topology, connection completeness, and calculates dynamic readiness score.",
            capabilities=["Topology verification", "Missing config detection", "Readiness score (0-100)", "Cycle check"],
        ),
        AgentInfo(
            id="error-detection-agent",
            name="Error Detection Agent",
            role="Error Diagnostician",
            description="Isolates failure root causes and generates the Diagnostic Triad with log evidence.",
            capabilities=["Failure isolation", "Diagnostic triad", "Log evidence extraction", "Stack trace analysis"],
        ),
        AgentInfo(
            id="self-repair-agent",
            name="Self-Repair Agent",
            role="Autonomous Repairer",
            description="Performs autonomous 5-stage workflow self-repair strictly capped at 2 attempts.",
            capabilities=["5-stage repair loop", "Targeted parameter injection", "Revalidation gate", "Retest verification"],
        ),
    ]


@router.post(
    "/plan",
    summary="Plan Workflow with Planner Agent",
    description="Generates a structured workflow graph from natural language prompt.",
)
def plan_workflow(payload: PlanRequest) -> Dict[str, Any]:
    agent = PlannerAgent()
    return agent.plan_workflow(payload.prompt, payload.requirements)


@router.post(
    "/research",
    summary="Collect Context with Research Agent",
    description="Gathers domain information or extracts entities from text/documents.",
)
def research_information(payload: ResearchRequest) -> Dict[str, Any]:
    agent = ResearchAgent()
    return agent.collect_information(payload.topic, payload.context)


@router.post(
    "/diagnose",
    summary="Diagnose Error with Error Detection Agent",
    description="Generates Diagnostic Triad and timestamped log evidence from failing steps.",
)
def diagnose_error(payload: DiagnoseRequest) -> Dict[str, Any]:
    agent = ErrorDetectionAgent()
    return agent.diagnose_failure(payload.workflow, payload.execution_steps, payload.error_message)


@router.post(
    "/repair",
    summary="Execute Self-Repair with Self-Repair Agent",
    description="Executes autonomous 5-stage repair and verification loop (max 2 attempts).",
)
def repair_workflow(payload: RepairRequest) -> Dict[str, Any]:
    agent = SelfRepairAgent()
    return agent.repair_workflow(payload.workflow, payload.diagnosis, payload.attempt)
