"""
AgentForge AI - Workflow API Endpoints (Member 3)
Exposes Component Library catalog, Workflow Generation from AI execution plans,
validation, version comparison, and targeted workflow modification.
"""

from typing import List, Dict, Any, Optional, Literal
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from app.schemas.workflow import WorkflowBase, WorkflowCreate
from app.services.ai import agent_architect, ArchitectExecutionPlan
from app.services.workflow import (
    component_library,
    workflow_generator,
    workflow_validator,
    workflow_modifier,
    compare_workflows,
    restore_version,
    rollback_to_version,
    ExecutionPlan,
    ValidationResult,
    WorkflowDiff,
)

router = APIRouter(prefix="/workflows", tags=["Workflows (Member 3)"])


# ---------------------------------------------------------------------------
# Request & Response Models
# ---------------------------------------------------------------------------

class ComponentSummary(BaseModel):
    type: str
    displayName: str
    category: str
    description: str
    icon: str
    defaultInputs: List[str]
    defaultOutputs: List[str]
    defaultConfig: Dict[str, Any]
    configFields: List[Dict[str, Any]]


class ComponentCatalogResponse(BaseModel):
    version: str = "1.0.0"
    total_components: int
    components: List[ComponentSummary]


class WorkflowValidationRequest(BaseModel):
    workflow: Dict[str, Any]


class GenerateFromPromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Natural language prompt describing agent behavior")
    model: Optional[str] = "gemini-1.5-pro"


class GenerateFromPromptResponse(BaseModel):
    workflow: WorkflowCreate
    execution_plan: Dict[str, Any]
    validation: ValidationResult


class WorkflowCompareRequest(BaseModel):
    v1: WorkflowBase
    v2: WorkflowBase


class WorkflowModifyRequest(BaseModel):
    workflow: WorkflowBase
    patch: Dict[str, Any] = Field(
        ...,
        description="Patch operations: update_configs, add_nodes, remove_nodes, add_edges, remove_edges, bump_version"
    )


class WorkflowModifyResponse(BaseModel):
    workflow: WorkflowBase
    diff: WorkflowDiff


class WorkflowRollbackRequest(BaseModel):
    current: WorkflowBase
    target: WorkflowBase
    bump_version: Literal["major", "minor", "patch"] = "minor"


class WorkflowRollbackResponse(BaseModel):
    workflow: WorkflowBase
    diff: WorkflowDiff


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/components",
    response_model=ComponentCatalogResponse,
    summary="List the 7 canonical workflow components and their schemas",
)
def get_component_catalog():
    """Returns the reusable component catalog for the 7 supported node types."""
    comps = component_library.list_components()
    summaries = []
    for c in comps:
        summaries.append(
            ComponentSummary(
                type=c.type,
                displayName=c.displayName,
                category=c.category.value,
                description=c.description,
                icon=c.icon,
                defaultInputs=c.defaultInputs,
                defaultOutputs=c.defaultOutputs,
                defaultConfig=c.defaultConfig,
                configFields=[f.model_dump() for f in c.configFields],
            )
        )
    return ComponentCatalogResponse(
        total_components=len(summaries),
        components=summaries,
    )


@router.post(
    "/generate",
    response_model=WorkflowCreate,
    status_code=status.HTTP_201_CREATED,
    summary="Generate executable workflow from Member 2 AI Execution Plan",
)
def generate_workflow(plan: Dict[str, Any]):
    """
    Transforms Member 2's structured AI execution plan into an executable
    workflow JSON conforming to shared/workflow.schema.json.
    Supports both Member 3 ExecutionPlan and Member 2 ArchitectExecutionPlan structures.
    """
    try:
        workflow = workflow_generator.generate(plan)
        return workflow
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to generate workflow: {str(e)}",
        )


@router.post(
    "/generate-from-prompt",
    response_model=GenerateFromPromptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Complete end-to-end pipeline: Natural language prompt -> Member 2 Architect -> Member 3 Generator -> Validated Workflow",
)
def generate_from_prompt(req: GenerateFromPromptRequest):
    """
    End-to-end generation endpoint:
    1. Member 2 Agent Architect analyzes natural language prompt and produces an ArchitectExecutionPlan.
    2. Member 3 Workflow Generator converts plan into React Flow compatible Workflow JSON.
    3. Member 3 Workflow Validator verifies topology, connections, handles, and configs.
    """
    try:
        plan = agent_architect.analyze_requirement(req.prompt)
        workflow = workflow_generator.generate(plan)
        validation = workflow_validator.validate(workflow)
        return GenerateFromPromptResponse(
            workflow=workflow,
            execution_plan=plan.model_dump(),
            validation=validation,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process natural language prompt: {str(e)}",
        )


@router.post(
    "/validate",
    response_model=ValidationResult,
    summary="Validate workflow structure, configs, handles, and topology",
)
def validate_workflow(payload: WorkflowValidationRequest):
    """
    Validates a visual workflow definition, returning comprehensive error and
    warning details with affected node and edge IDs.
    """
    return workflow_validator.validate(payload.workflow)


@router.post(
    "/compare",
    response_model=WorkflowDiff,
    summary="Compare two workflow revisions and compute structured diff",
)
def compare_workflow_versions(req: WorkflowCompareRequest):
    """
    Compares two workflow versions (v1 and v2) and returns tracked differences:
    added/removed/modified nodes, edges, configs, and compatibility flag.
    """
    return compare_workflows(req.v1, req.v2)


@router.post(
    "/modify",
    response_model=WorkflowModifyResponse,
    summary="Apply targeted modifications or self-repair patches to a workflow",
)
def modify_workflow(req: WorkflowModifyRequest):
    """
    Applies targeted modifications (updating node configs, adding/removing nodes or edges)
    and returns the new workflow version alongside the computed diff.
    """
    try:
        updated_wf, diff = workflow_modifier.apply_patch(req.workflow, req.patch)
        return WorkflowModifyResponse(workflow=updated_wf, diff=diff)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to apply modification patch: {str(e)}",
        )


@router.post(
    "/rollback",
    response_model=WorkflowRollbackResponse,
    summary="Rollback workflow to an earlier version while tracking changes",
)
def rollback_workflow(req: WorkflowRollbackRequest):
    """
    Rolls back the current workflow to the topology and configuration of target_version,
    creating a new forward version preserving node IDs, connections, and configurations
    without mutating the original historical version.
    """
    try:
        rolled_back_wf, diff = rollback_to_version(
            current_workflow=req.current,
            target_version_workflow=req.target,
            bump=req.bump_version,
        )
        return WorkflowRollbackResponse(workflow=rolled_back_wf, diff=diff)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to rollback workflow: {str(e)}",
        )
