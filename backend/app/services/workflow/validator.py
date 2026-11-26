"""
AgentForge AI - Workflow Validation Module (Member 3)
Performs deep structural, configuration, connection, and topology validation
on visual workflow definitions.
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Set, Union
from pydantic import BaseModel, Field

from app.schemas.workflow import WorkflowBase, WorkflowNodeSchema, WorkflowEdgeSchema
from app.services.workflow.components import component_library


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationCategory(str, Enum):
    STRUCTURAL = "structural"
    CONFIGURATION = "configuration"
    CONNECTION = "connection"
    TOPOLOGY = "topology"


class ValidationIssue(BaseModel):
    """Specific error or warning identified during workflow validation."""
    id: str
    node_id: Optional[str] = None
    edge_id: Optional[str] = None
    component_name: Optional[str] = None
    category: ValidationCategory
    severity: ValidationSeverity
    title: str
    description: str
    suggested_fix: str
    can_auto_fix: bool = False


class ValidationMetrics(BaseModel):
    """Summary metrics of the workflow topology and health."""
    total_nodes: int = 0
    total_edges: int = 0
    supported_nodes_count: int = 0
    unsupported_nodes_count: int = 0
    disconnected_nodes_count: int = 0
    has_input_node: bool = False
    has_output_node: bool = False
    has_cycles: bool = False
    error_count: int = 0
    warning_count: int = 0


class ValidationResult(BaseModel):
    """Complete validation result report."""
    is_valid: bool
    errors: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    metrics: ValidationMetrics = Field(default_factory=ValidationMetrics)

    def summary(self) -> str:
        if self.is_valid:
            return f"Workflow valid ({self.metrics.total_nodes} nodes, {self.metrics.total_edges} edges, {len(self.warnings)} warnings)."
        return f"Workflow validation failed with {len(self.errors)} error(s) and {len(self.warnings)} warning(s)."


class WorkflowValidator:
    """Comprehensive Workflow Validator for Member 3."""

    def __init__(self):
        self.library = component_library

    def validate(self, workflow: Union[WorkflowBase, Dict[str, Any]]) -> ValidationResult:
        """
        Validate a workflow instance or dictionary against structural,
        configuration, connection, and topology rules.
        """
        if isinstance(workflow, dict):
            # Support both flattened WorkflowBase and canonical shared/workflow.schema.json with "metadata"
            if "metadata" in workflow and isinstance(workflow["metadata"], dict):
                meta = workflow["metadata"]
                flattened = {
                    "name": meta.get("name", "Untitled Workflow"),
                    "description": meta.get("description"),
                    "version": meta.get("version", "1.0.0"),
                    "tags": meta.get("tags", []),
                    "configuration": workflow.get("configuration", {}),
                    "nodes": workflow.get("nodes", []),
                    "edges": workflow.get("edges", []),
                }
                try:
                    wf = WorkflowBase(**flattened)
                except Exception as e:
                    return ValidationResult(
                        is_valid=False,
                        errors=[
                            ValidationIssue(
                                id="schema_syntax_error",
                                category=ValidationCategory.STRUCTURAL,
                                severity=ValidationSeverity.ERROR,
                                title="Invalid Workflow Schema",
                                description=f"Workflow payload could not be parsed: {str(e)}",
                                suggested_fix="Ensure all required fields (metadata, nodes, edges) conform to schema.",
                            )
                        ],
                        metrics=ValidationMetrics(error_count=1),
                    )
            else:
                try:
                    wf = WorkflowBase(**workflow)
                except Exception as e:
                    return ValidationResult(
                        is_valid=False,
                        errors=[
                            ValidationIssue(
                                id="schema_syntax_error",
                                category=ValidationCategory.STRUCTURAL,
                                severity=ValidationSeverity.ERROR,
                                title="Invalid Workflow Schema",
                                description=f"Workflow payload could not be parsed: {str(e)}",
                                suggested_fix="Ensure all required fields (name, nodes, edges) conform to schema.",
                            )
                        ],
                        metrics=ValidationMetrics(error_count=1),
                    )
        else:
            wf = workflow

        errors: List[ValidationIssue] = []
        warnings: List[ValidationIssue] = []

        nodes = wf.nodes or []
        edges = wf.edges or []

        # -------------------------------------------------------------------
        # 1. Structural Checks: Node Presence & Uniqueness
        # -------------------------------------------------------------------
        if not nodes:
            errors.append(
                ValidationIssue(
                    id="empty_workflow",
                    category=ValidationCategory.STRUCTURAL,
                    severity=ValidationSeverity.ERROR,
                    title="Empty Workflow",
                    description="Workflow contains zero nodes. At least one node is required.",
                    suggested_fix="Add at least an Input and Output node to start the workflow.",
                )
            )

        seen_node_ids: Set[str] = set()
        duplicate_node_ids: Set[str] = set()
        node_map: Dict[str, WorkflowNodeSchema] = {}

        for node in nodes:
            if not node.id or not str(node.id).strip():
                errors.append(
                    ValidationIssue(
                        id=f"missing_node_id_{len(errors)}",
                        category=ValidationCategory.STRUCTURAL,
                        severity=ValidationSeverity.ERROR,
                        title="Missing Node Identifier",
                        description=f"Node '{node.name}' has no valid unique ID.",
                        suggested_fix="Assign a unique alphanumeric ID to the node.",
                    )
                )
                continue

            if node.id in seen_node_ids:
                duplicate_node_ids.add(node.id)
            else:
                seen_node_ids.add(node.id)
                node_map[node.id] = node

        for dup_id in duplicate_node_ids:
            errors.append(
                ValidationIssue(
                    id=f"duplicate_node_id_{dup_id}",
                    node_id=dup_id,
                    category=ValidationCategory.STRUCTURAL,
                    severity=ValidationSeverity.ERROR,
                    title="Duplicate Node ID",
                    description=f"Duplicate node ID detected: '{dup_id}'. Every node must have a unique identifier.",
                    suggested_fix=f"Rename duplicate nodes using unique suffixes (e.g. '{dup_id}_2').",
                    can_auto_fix=True,
                )
            )

        # -------------------------------------------------------------------
        # 2. Component Type & Configuration Validation
        # -------------------------------------------------------------------
        supported_count = 0
        unsupported_count = 0

        for node in nodes:
            if not self.library.is_supported(node.type):
                unsupported_count += 1
                errors.append(
                    ValidationIssue(
                        id=f"unsupported_type_{node.id}",
                        node_id=node.id,
                        component_name=node.name,
                        category=ValidationCategory.CONFIGURATION,
                        severity=ValidationSeverity.ERROR,
                        title="Unsupported Component Type",
                        description=f"Node '{node.id}' uses unsupported component type '{node.type}'. Supported types: {self.library.list_types()}.",
                        suggested_fix=f"Change node type to one of: {', '.join(self.library.list_types())}.",
                    )
                )
                continue

            supported_count += 1
            comp_def = self.library.get(node.type)
            if comp_def:
                try:
                    comp_def.validate_config(node.config or {})
                except Exception as ex:
                    errors.append(
                        ValidationIssue(
                            id=f"invalid_config_{node.id}",
                            node_id=node.id,
                            component_name=node.name,
                            category=ValidationCategory.CONFIGURATION,
                            severity=ValidationSeverity.ERROR,
                            title="Invalid Node Configuration",
                            description=f"Configuration for node '{node.id}' ({node.type}) failed validation: {str(ex)}",
                            suggested_fix=f"Ensure required parameters for {node.type} are provided and conform to validation rules.",
                            can_auto_fix=False,
                        )
                    )

        # -------------------------------------------------------------------
        # 3. Edge Integrity & Connection Checks
        # -------------------------------------------------------------------
        seen_edge_ids: Set[str] = set()
        incoming_edges: Dict[str, List[WorkflowEdgeSchema]] = {n.id: [] for n in nodes}
        outgoing_edges: Dict[str, List[WorkflowEdgeSchema]] = {n.id: [] for n in nodes}

        for edge in edges:
            # Check edge ID uniqueness
            if edge.id in seen_edge_ids:
                warnings.append(
                    ValidationIssue(
                        id=f"duplicate_edge_id_{edge.id}",
                        edge_id=edge.id,
                        category=ValidationCategory.CONNECTION,
                        severity=ValidationSeverity.WARNING,
                        title="Duplicate Edge ID",
                        description=f"Edge ID '{edge.id}' is repeated in the workflow definition.",
                        suggested_fix="Assign unique IDs to all edges.",
                        can_auto_fix=True,
                    )
                )
            seen_edge_ids.add(edge.id)

            # Check source and target existence
            src_exists = edge.source in node_map
            tgt_exists = edge.target in node_map

            if not src_exists or not tgt_exists:
                missing_part = []
                if not src_exists:
                    missing_part.append(f"source '{edge.source}'")
                if not tgt_exists:
                    missing_part.append(f"target '{edge.target}'")

                errors.append(
                    ValidationIssue(
                        id=f"invalid_connection_{edge.id}",
                        edge_id=edge.id,
                        category=ValidationCategory.CONNECTION,
                        severity=ValidationSeverity.ERROR,
                        title="Invalid Edge Connection",
                        description=f"Edge '{edge.id}' connects non-existent {', '.join(missing_part)}.",
                        suggested_fix="Ensure edge source and target reference valid existing node IDs.",
                        can_auto_fix=True,
                    )
                )
                continue

            # Check self-loops
            if edge.source == edge.target:
                errors.append(
                    ValidationIssue(
                        id=f"self_loop_{edge.id}",
                        edge_id=edge.id,
                        node_id=edge.source,
                        category=ValidationCategory.CONNECTION,
                        severity=ValidationSeverity.ERROR,
                        title="Self-Loop Connection Detected",
                        description=f"Edge '{edge.id}' creates a direct self-loop on node '{edge.source}'.",
                        suggested_fix="Remove the self-connecting edge to prevent infinite execution cycles.",
                        can_auto_fix=True,
                    )
                )

            # Record connections
            incoming_edges[edge.target].append(edge)
            outgoing_edges[edge.source].append(edge)

            # Validate handles if specified
            src_node = node_map[edge.source]
            tgt_node = node_map[edge.target]

            if edge.sourceHandle and src_node.outputHandles:
                if edge.sourceHandle not in src_node.outputHandles:
                    warnings.append(
                        ValidationIssue(
                            id=f"unknown_source_handle_{edge.id}",
                            edge_id=edge.id,
                            node_id=edge.source,
                            category=ValidationCategory.CONNECTION,
                            severity=ValidationSeverity.WARNING,
                            title="Unknown Source Handle",
                            description=f"Edge '{edge.id}' references source handle '{edge.sourceHandle}' which is not in node '{src_node.id}' outputHandles {src_node.outputHandles}.",
                            suggested_fix=f"Connect to one of the defined output handles: {src_node.outputHandles}.",
                        )
                    )

            if edge.targetHandle and tgt_node.inputHandles:
                if edge.targetHandle not in tgt_node.inputHandles:
                    warnings.append(
                        ValidationIssue(
                            id=f"unknown_target_handle_{edge.id}",
                            edge_id=edge.id,
                            node_id=edge.target,
                            category=ValidationCategory.CONNECTION,
                            severity=ValidationSeverity.WARNING,
                            title="Unknown Target Handle",
                            description=f"Edge '{edge.id}' references target handle '{edge.targetHandle}' which is not in node '{tgt_node.id}' inputHandles {tgt_node.inputHandles}.",
                            suggested_fix=f"Connect to one of the defined input handles: {tgt_node.inputHandles}.",
                        )
                    )

            # Role-specific connection rules:
            # - Input node should not have incoming edges
            if tgt_node.type == "Input":
                warnings.append(
                    ValidationIssue(
                        id=f"input_has_incoming_{edge.id}",
                        edge_id=edge.id,
                        node_id=tgt_node.id,
                        category=ValidationCategory.CONNECTION,
                        severity=ValidationSeverity.WARNING,
                        title="Incoming Edge to Input Node",
                        description=f"Input node '{tgt_node.id}' typically receives external triggers rather than incoming workflow edges.",
                        suggested_fix="Verify if this node should be an intermediate step or starting trigger.",
                    )
                )

            # - Output node should not have outgoing edges
            if src_node.type == "Output":
                warnings.append(
                    ValidationIssue(
                        id=f"output_has_outgoing_{edge.id}",
                        edge_id=edge.id,
                        node_id=src_node.id,
                        category=ValidationCategory.CONNECTION,
                        severity=ValidationSeverity.WARNING,
                        title="Outgoing Edge from Terminal Output Node",
                        description=f"Output node '{src_node.id}' is a terminal node and should not produce downstream edges.",
                        suggested_fix="Remove downstream connections from terminal Output nodes.",
                    )
                )

        # -------------------------------------------------------------------
        # 4. Topology Checks: Orphaned & Disconnected Nodes
        # -------------------------------------------------------------------
        disconnected_count = 0
        has_input = any(n.type == "Input" for n in nodes)
        has_output = any(n.type == "Output" for n in nodes)

        if not has_input and len(nodes) > 1:
            warnings.append(
                ValidationIssue(
                    id="missing_input_node",
                    category=ValidationCategory.TOPOLOGY,
                    severity=ValidationSeverity.WARNING,
                    title="Missing Input Node",
                    description="Workflow does not contain an 'Input' node to receive initial parameters.",
                    suggested_fix="Add an Input component to capture user prompts or payload.",
                )
            )

        if not has_output and len(nodes) > 1:
            warnings.append(
                ValidationIssue(
                    id="missing_output_node",
                    category=ValidationCategory.TOPOLOGY,
                    severity=ValidationSeverity.WARNING,
                    title="Missing Output Node",
                    description="Workflow does not contain an 'Output' node to deliver final results.",
                    suggested_fix="Add an Output component as the terminal step.",
                )
            )

        # Check for isolated/disconnected nodes (no incoming and no outgoing)
        if len(nodes) > 1:
            for node in nodes:
                in_count = len(incoming_edges.get(node.id, []))
                out_count = len(outgoing_edges.get(node.id, []))

                if in_count == 0 and out_count == 0:
                    disconnected_count += 1
                    errors.append(
                        ValidationIssue(
                            id=f"disconnected_node_{node.id}",
                            node_id=node.id,
                            component_name=node.name,
                            category=ValidationCategory.TOPOLOGY,
                            severity=ValidationSeverity.ERROR,
                            title="Disconnected / Orphaned Node",
                            description=f"Node '{node.id}' ({node.name}) has no incoming or outgoing connections.",
                            suggested_fix="Connect this component to the workflow graph or remove it.",
                            can_auto_fix=True,
                        )
                    )
                elif node.type != "Input" and in_count == 0:
                    warnings.append(
                        ValidationIssue(
                            id=f"unreachable_node_{node.id}",
                            node_id=node.id,
                            component_name=node.name,
                            category=ValidationCategory.TOPOLOGY,
                            severity=ValidationSeverity.WARNING,
                            title="Node Has No Incoming Connection",
                            description=f"Non-input node '{node.id}' ({node.type}) has no incoming connections and may never execute.",
                            suggested_fix="Connect an upstream node to this component.",
                        )
                    )
                elif node.type != "Output" and out_count == 0:
                    warnings.append(
                        ValidationIssue(
                            id=f"dead_end_node_{node.id}",
                            node_id=node.id,
                            component_name=node.name,
                            category=ValidationCategory.TOPOLOGY,
                            severity=ValidationSeverity.WARNING,
                            title="Dead-End Node",
                            description=f"Non-terminal node '{node.id}' ({node.type}) has no outgoing connections.",
                            suggested_fix="Connect this node to subsequent steps or an Output node.",
                        )
                    )

        # -------------------------------------------------------------------
        # 5. Cycle Detection (DFS)
        # -------------------------------------------------------------------
        has_cycles = self._detect_cycles(nodes, outgoing_edges)
        if has_cycles and wf.configuration.executionMode in ("dag", "sequential"):
            warnings.append(
                ValidationIssue(
                    id="cycle_in_dag_mode",
                    category=ValidationCategory.TOPOLOGY,
                    severity=ValidationSeverity.WARNING,
                    title="Cycle Detected in DAG Mode",
                    description="Graph contains cycles/loops, but executionMode is set to 'dag' or 'sequential'.",
                    suggested_fix="Set executionMode to 'langgraph' or eliminate the loop to maintain a DAG.",
                )
            )

        # -------------------------------------------------------------------
        # 6. Aggregate Results
        # -------------------------------------------------------------------
        metrics = ValidationMetrics(
            total_nodes=len(nodes),
            total_edges=len(edges),
            supported_nodes_count=supported_count,
            unsupported_nodes_count=unsupported_count,
            disconnected_nodes_count=disconnected_count,
            has_input_node=has_input,
            has_output_node=has_output,
            has_cycles=has_cycles,
            error_count=len(errors),
            warning_count=len(warnings),
        )

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metrics=metrics,
        )

    def _detect_cycles(
        self,
        nodes: List[WorkflowNodeSchema],
        outgoing: Dict[str, List[WorkflowEdgeSchema]],
    ) -> bool:
        """DFS cycle detection across all connected components."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for edge in outgoing.get(node_id, []):
                neighbor = edge.target
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node in nodes:
            if node.id not in visited:
                if dfs(node.id):
                    return True
        return False


# Global singleton instance
workflow_validator = WorkflowValidator()
