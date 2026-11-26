"""
AgentForge AI - Workflow Generation Engine (Member 3)
Transforms structured execution plans from Member 2 into executable,
React Flow-ready workflow JSON conforming to shared/workflow.schema.json.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field

from app.schemas.workflow import (
    NodeType,
    NodePosition,
    WorkflowNodeSchema,
    WorkflowEdgeSchema,
    WorkflowConfigurationSchema,
    WorkflowBase,
    WorkflowCreate,
)
from app.services.workflow.components import component_library


class ExecutionPlanStep(BaseModel):
    """A step within Member 2's structured AI execution plan."""
    id: Optional[str] = None
    step_id: Optional[str] = None
    title: str = Field(..., min_length=1)
    description: Optional[str] = ""
    component_type: str = Field(..., description="One of the 7 supported NodeType strings")
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)
    next_steps: List[str] = Field(
        default_factory=list,
        description="IDs or titles of subsequent steps to connect to"
    )
    branch_conditions: Optional[Dict[str, str]] = Field(
        default=None,
        description="For Condition or branching nodes, mapping condition value (e.g. 'true', 'false') to target step identifier"
    )

    def get_identifier(self) -> str:
        return self.id or self.step_id or self.title


class ExecutionPlan(BaseModel):
    """The structured execution plan contract produced by Member 2."""
    plan_id: Optional[str] = None
    name: str = Field(default="Generated Agent Workflow", min_length=1)
    description: Optional[str] = "Workflow generated from AI execution plan."
    goal: Optional[str] = None
    version: str = "1.0.0"
    steps: List[ExecutionPlanStep] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    configuration: Optional[Dict[str, Any]] = None


class WorkflowGenerator:
    """Core Workflow Generation Engine for Member 3."""

    def __init__(self):
        self.library = component_library

    def generate(self, plan: Union[ExecutionPlan, Any, Dict[str, Any]]) -> WorkflowCreate:
        """
        Convert a Member 2 ExecutionPlan or ArchitectExecutionPlan into an executable WorkflowCreate object.
        """
        parsed_plan = self._adapt_execution_plan(plan)

        nodes: List[WorkflowNodeSchema] = []
        edges: List[WorkflowEdgeSchema] = []

        step_to_node_id: Dict[str, str] = {}
        node_type_counts: Dict[str, int] = {}

        # 1. First pass: Assign unique node IDs and instantiate nodes
        for idx, step in enumerate(parsed_plan.steps):
            raw_type = step.component_type.strip()
            # Normalize casing if needed
            matched_type = self._normalize_component_type(raw_type)

            node_type_counts[matched_type] = node_type_counts.get(matched_type, 0) + 1
            node_slug = matched_type.lower().replace(" ", "_")
            node_id = f"node_{node_slug}_{node_type_counts[matched_type]}"

            # Map all possible step references to this unique node ID
            step_to_node_id[node_id] = node_id
            if step.id:
                step_to_node_id[step.id] = node_id
            if step.step_id:
                step_to_node_id[step.step_id] = node_id
            step_to_node_id[step.title] = node_id
            step_to_node_id[str(idx)] = node_id

            # Layout positioning for React Flow (horizontal flow with vertical branching)
            pos_x = 80.0 + (idx * 260.0)
            pos_y = 150.0 + ((idx % 2) * 40.0)
            position = NodePosition(x=pos_x, y=pos_y)

            # Retrieve default config and handles from ComponentLibrary
            comp_def = self.library.get(matched_type)
            merged_config: Dict[str, Any] = {}
            default_inputs: List[str] = []
            default_outputs: List[str] = []

            if comp_def:
                merged_config.update(comp_def.defaultConfig)
                default_inputs = list(comp_def.defaultInputs)
                default_outputs = list(comp_def.defaultOutputs)

            # Override with step-specific config
            if step.config:
                merged_config.update(step.config)

            # Determine handles
            input_handles = step.inputs if step.inputs else default_inputs
            output_handles = step.outputs if step.outputs else default_outputs

            node = WorkflowNodeSchema(
                id=node_id,
                type=matched_type,  # type: ignore
                name=step.title,
                position=position,
                config=merged_config,
                inputHandles=input_handles,
                outputHandles=output_handles,
            )
            nodes.append(node)

        # 2. Second pass: Generate edges/connections
        edge_counter = 1
        for idx, step in enumerate(parsed_plan.steps):
            src_node_id = step_to_node_id.get(step.get_identifier()) or step_to_node_id.get(str(idx))
            if not src_node_id:
                continue

            src_node = next((n for n in nodes if n.id == src_node_id), None)
            src_outputs = src_node.outputHandles if src_node else []

            # Handle conditional branching
            if step.branch_conditions:
                for cond_key, target_ref in step.branch_conditions.items():
                    target_node_id = step_to_node_id.get(target_ref)
                    if target_node_id and target_node_id != src_node_id:
                        edge_id = f"edge_{edge_counter}_{src_node_id}_{target_node_id}"
                        edge_counter += 1

                        # Match handle to condition key if available
                        src_handle = cond_key if cond_key in src_outputs else (src_outputs[0] if src_outputs else None)

                        edges.append(
                            WorkflowEdgeSchema(
                                id=edge_id,
                                source=src_node_id,
                                target=target_node_id,
                                sourceHandle=src_handle,
                                condition=cond_key,
                            )
                        )

            # Handle explicit next_steps
            elif step.next_steps:
                for target_ref in step.next_steps:
                    target_node_id = step_to_node_id.get(target_ref)
                    if target_node_id and target_node_id != src_node_id:
                        edge_id = f"edge_{edge_counter}_{src_node_id}_{target_node_id}"
                        edge_counter += 1
                        src_handle = src_outputs[0] if src_outputs else None
                        edges.append(
                            WorkflowEdgeSchema(
                                id=edge_id,
                                source=src_node_id,
                                target=target_node_id,
                                sourceHandle=src_handle,
                            )
                        )

            # If no explicit links, connect sequentially to the next node by default
            elif idx + 1 < len(nodes):
                target_node_id = nodes[idx + 1].id
                edge_id = f"edge_{edge_counter}_{src_node_id}_{target_node_id}"
                edge_counter += 1
                src_handle = src_outputs[0] if src_outputs else None
                edges.append(
                    WorkflowEdgeSchema(
                        id=edge_id,
                        source=src_node_id,
                        target=target_node_id,
                        sourceHandle=src_handle,
                    )
                )

        # 3. Build workflow-level configuration
        config_dict = parsed_plan.configuration or {}
        workflow_config = WorkflowConfigurationSchema(
            timeoutSeconds=config_dict.get("timeoutSeconds", 300),
            maxRetries=config_dict.get("maxRetries", 2),
            autoRepairEnabled=config_dict.get("autoRepairEnabled", True),
            executionMode=config_dict.get("executionMode", "langgraph"),
            collectMetrics=config_dict.get("collectMetrics", True),
        )

        # 4. Construct complete WorkflowCreate
        description = parsed_plan.description or (f"Goal: {parsed_plan.goal}" if parsed_plan.goal else "Generated visual workflow")
        tags = list(parsed_plan.tags)
        if "generated" not in tags:
            tags.append("generated")

        return WorkflowCreate(
            name=parsed_plan.name,
            description=description,
            version=parsed_plan.version or "1.0.0",
            configuration=workflow_config,
            nodes=nodes,
            edges=edges,
            tags=tags,
        )

    def to_workflow_definition(
        self,
        workflow: WorkflowBase,
        workflow_id: Optional[str] = None,
        author: str = "Member 2 / AI Architect",
    ) -> Dict[str, Any]:
        """
        Export a WorkflowBase/WorkflowCreate instance into the canonical
        shared/workflow.schema.json format with schemaVersion and metadata object.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        return {
            "schemaVersion": "1.0.0",
            "metadata": {
                "id": workflow_id or str(uuid.uuid4()),
                "name": workflow.name,
                "description": workflow.description or "",
                "version": workflow.version,
                "tags": workflow.tags or [],
                "author": author,
                "createdAt": now_iso,
                "updatedAt": now_iso,
            },
            "configuration": workflow.configuration.model_dump(),
            "nodes": [n.model_dump() for n in workflow.nodes],
            "edges": [e.model_dump() for e in workflow.edges],
        }

    def from_workflow_definition(self, definition: Dict[str, Any]) -> WorkflowCreate:
        """
        Convert a canonical shared/workflow.schema.json dictionary back into
        WorkflowCreate for persistence and execution.
        """
        metadata = definition.get("metadata", {})
        config_dict = definition.get("configuration", {})
        return WorkflowCreate(
            name=metadata.get("name", "Untitled Workflow"),
            description=metadata.get("description"),
            version=metadata.get("version", "1.0.0"),
            tags=metadata.get("tags", []),
            configuration=WorkflowConfigurationSchema(**config_dict),
            nodes=[WorkflowNodeSchema(**n) for n in definition.get("nodes", [])],
            edges=[WorkflowEdgeSchema(**e) for e in definition.get("edges", [])],
        )

    def _adapt_execution_plan(self, plan: Any) -> ExecutionPlan:
        """
        Coordinates the data contract between Member 2 (AI Architect) and Member 3 (Generator).
        Converts ArchitectExecutionPlan, ExecutionPlan, or raw dictionaries into canonical ExecutionPlan.
        """
        if isinstance(plan, ExecutionPlan):
            return plan

        if hasattr(plan, "model_dump"):
            data = plan.model_dump()
        elif isinstance(plan, dict):
            data = dict(plan)
        else:
            raise TypeError(f"Unsupported execution plan type: {type(plan)}")

        # Map top-level attributes
        name = data.get("name") or data.get("agent_name") or data.get("title") or "Synthesized Agent Workflow"
        description = data.get("description") or data.get("goal") or "Workflow generated from AI execution plan."
        goal = data.get("goal")
        version = data.get("version", "1.0.0")
        tags = data.get("tags", [])
        config = data.get("configuration")

        # Map steps
        raw_steps = data.get("steps", [])
        adapted_steps: List[ExecutionPlanStep] = []

        for step in raw_steps:
            if hasattr(step, "model_dump"):
                s_data = step.model_dump()
            elif isinstance(step, dict):
                s_data = dict(step)
            else:
                continue

            s_id = s_data.get("id") or s_data.get("step_id")
            s_title = s_data.get("title") or s_data.get("name") or s_data.get("step_name") or "Workflow Step"
            s_type = s_data.get("component_type") or s_data.get("node_type") or s_data.get("type") or "LLM"
            s_config = s_data.get("config") or s_data.get("parameters") or s_data.get("settings") or {}
            s_next = s_data.get("next_steps") or s_data.get("targets") or []
            s_branches = s_data.get("branch_conditions") or s_data.get("branches")

            adapted_steps.append(
                ExecutionPlanStep(
                    id=s_id,
                    step_id=s_id,
                    title=s_title,
                    description=s_data.get("description", ""),
                    component_type=s_type,
                    inputs=s_data.get("inputs", []),
                    outputs=s_data.get("outputs", []),
                    config=s_config,
                    next_steps=s_next,
                    branch_conditions=s_branches,
                )
            )

        return ExecutionPlan(
            plan_id=data.get("plan_id"),
            name=name,
            description=description,
            goal=goal,
            version=version,
            steps=adapted_steps,
            tags=tags,
            configuration=config,
        )

    def _normalize_component_type(self, raw_type: str) -> str:
        """Resolve case-insensitive or partial type strings to canonical 7 node types."""
        type_mapping = {
            "input": "Input",
            "llm": "LLM",
            "gemini": "LLM",
            "ai": "LLM",
            "document reader": "Document Reader",
            "document_reader": "Document Reader",
            "docreader": "Document Reader",
            "doc_reader": "Document Reader",
            "reader": "Document Reader",
            "tool": "Tool",
            "api": "Tool",
            "condition": "Condition",
            "branch": "Condition",
            "decision": "Condition",
            "human approval": "Human Approval",
            "human_approval": "Human Approval",
            "approval": "Human Approval",
            "human": "Human Approval",
            "output": "Output",
        }
        normalized = type_mapping.get(raw_type.lower())
        if normalized and self.library.is_supported(normalized):
            return normalized

        # If already exactly matches a registered type
        if self.library.is_supported(raw_type):
            return raw_type

        # Return as-is so validator will report clean unsupported error
        return raw_type


# Global singleton instance
workflow_generator = WorkflowGenerator()
