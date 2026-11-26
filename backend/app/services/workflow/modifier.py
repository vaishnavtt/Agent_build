"""
AgentForge AI - Targeted Workflow Modification & Repair (Member 3)
Provides pure, immutable modification operations on workflows, supporting
fine-grained updates (prompts, configurations, added/removed nodes and edges)
and automated patch applications for self-repair loops.
"""

import copy
import uuid
from typing import Dict, List, Any, Optional, Tuple, Literal, Union
from pydantic import BaseModel, Field

from app.schemas.workflow import (
    WorkflowBase,
    WorkflowNodeSchema,
    WorkflowEdgeSchema,
    NodePosition,
)
from app.services.workflow.components import component_library
from app.services.workflow.versioning import increment_version, compare_workflows, WorkflowDiff
from app.services.workflow.validator import workflow_validator


class WorkflowModifier:
    """Provides targeted, immutable modification methods on workflows."""

    def __init__(self):
        self.library = component_library
        self.validator = workflow_validator

    def validate_modification(self, workflow: WorkflowBase) -> None:
        """
        Validates modification rules:
        - All node types are supported canonical types
        - All node configs conform to schema
        - All edges reference valid existing nodes
        - No self-loops
        """
        node_ids = {n.id for n in workflow.nodes}
        for n in workflow.nodes:
            if not self.library.is_supported(n.type):
                raise ValueError(f"Unsupported component type '{n.type}' on node '{n.id}'.")
            self.library.validate_node_config(n.type, n.config or {})

        for e in workflow.edges:
            if e.source not in node_ids:
                raise ValueError(f"Invalid reference: Edge '{e.id}' references nonexistent source '{e.source}'.")
            if e.target not in node_ids:
                raise ValueError(f"Invalid reference: Edge '{e.id}' references nonexistent target '{e.target}'.")
            if e.source == e.target:
                raise ValueError(f"Malformed connection: Edge '{e.id}' creates an invalid self-loop on '{e.source}'.")

    def update_node_config(
        self,
        workflow: WorkflowBase,
        node_id: str,
        config_updates: Dict[str, Any],
        bump_version: Literal["major", "minor", "patch"] = "patch",
    ) -> WorkflowBase:
        """
        Update configuration parameters of a specific node (e.g. LLM prompt, model, temperature).
        Returns a new WorkflowBase copy with incremented version.
        """
        cloned = copy.deepcopy(workflow)
        node_found = False

        for node in cloned.nodes:
            if node.id == node_id:
                node_found = True
                new_config = dict(node.config or {})
                new_config.update(config_updates)
                # Validate updated config against component library
                validated = self.library.validate_node_config(node.type, new_config)
                node.config = validated
                break

        if not node_found:
            raise ValueError(f"Node '{node_id}' not found in workflow '{workflow.name}'.")

        cloned.version = increment_version(cloned.version, bump=bump_version)
        self.validate_modification(cloned)
        return cloned

    def update_node(
        self,
        workflow: WorkflowBase,
        node_id: str,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        position: Optional[Tuple[float, float]] = None,
        input_handles: Optional[List[str]] = None,
        output_handles: Optional[List[str]] = None,
        bump_version: Literal["major", "minor", "patch"] = "patch",
    ) -> WorkflowBase:
        """
        Update multiple attributes of a node (name, config, position, handles).
        """
        cloned = copy.deepcopy(workflow)
        target_node: Optional[WorkflowNodeSchema] = None

        for node in cloned.nodes:
            if node.id == node_id:
                target_node = node
                break

        if not target_node:
            raise ValueError(f"Node '{node_id}' not found.")

        if name is not None:
            target_node.name = name
        if position is not None:
            target_node.position = NodePosition(x=position[0], y=position[1])
        if input_handles is not None:
            target_node.inputHandles = list(input_handles)
        if output_handles is not None:
            target_node.outputHandles = list(output_handles)
        if config is not None:
            merged = dict(target_node.config or {})
            merged.update(config)
            target_node.config = self.library.validate_node_config(target_node.type, merged)

        cloned.version = increment_version(cloned.version, bump=bump_version)
        self.validate_modification(cloned)
        return cloned

    def add_node(
        self,
        workflow: WorkflowBase,
        node: Union[WorkflowNodeSchema, Dict[str, Any]],
        connect_after_node_id: Optional[str] = None,
        connect_before_node_id: Optional[str] = None,
        bump_version: Literal["major", "minor", "patch"] = "minor",
    ) -> WorkflowBase:
        """
        Add a new node to the workflow and optionally connect it into existing topology.
        """
        cloned = copy.deepcopy(workflow)

        if isinstance(node, dict):
            node_dict = dict(node)
            if "id" not in node_dict or not node_dict["id"]:
                node_type = node_dict.get("type", "node").lower().replace(" ", "_")
                node_dict["id"] = f"node_{node_type}_{uuid.uuid4().hex[:6]}"
            new_node = WorkflowNodeSchema(**node_dict)
        else:
            new_node = copy.deepcopy(node)

        # Check unique ID
        if any(n.id == new_node.id for n in cloned.nodes):
            new_node.id = f"{new_node.id}_{uuid.uuid4().hex[:6]}"

        # Validate config
        new_node.config = self.library.validate_node_config(new_node.type, new_node.config or {})
        cloned.nodes.append(new_node)

        # Connect after a specified node
        if connect_after_node_id:
            src = next((n for n in cloned.nodes if n.id == connect_after_node_id), None)
            if src:
                src_handle = src.outputHandles[0] if src.outputHandles else None
                tgt_handle = new_node.inputHandles[0] if new_node.inputHandles else None
                edge_id = f"edge_{src.id}_{new_node.id}_{uuid.uuid4().hex[:4]}"
                cloned.edges.append(
                    WorkflowEdgeSchema(
                        id=edge_id,
                        source=src.id,
                        target=new_node.id,
                        sourceHandle=src_handle,
                        targetHandle=tgt_handle,
                    )
                )

        # Connect before a specified node
        if connect_before_node_id:
            tgt = next((n for n in cloned.nodes if n.id == connect_before_node_id), None)
            if tgt:
                src_handle = new_node.outputHandles[0] if new_node.outputHandles else None
                tgt_handle = tgt.inputHandles[0] if tgt.inputHandles else None
                edge_id = f"edge_{new_node.id}_{tgt.id}_{uuid.uuid4().hex[:4]}"
                cloned.edges.append(
                    WorkflowEdgeSchema(
                        id=edge_id,
                        source=new_node.id,
                        target=tgt.id,
                        sourceHandle=src_handle,
                        targetHandle=tgt_handle,
                    )
                )

        cloned.version = increment_version(cloned.version, bump=bump_version)
        self.validate_modification(cloned)
        return cloned

    def remove_node(
        self,
        workflow: WorkflowBase,
        node_id: str,
        reconnect: bool = False,
        bump_version: Literal["major", "minor", "patch"] = "minor",
    ) -> WorkflowBase:
        """
        Remove a node by ID. If reconnect is True, connects incoming sources to outgoing targets.
        """
        cloned = copy.deepcopy(workflow)

        target = next((n for n in cloned.nodes if n.id == node_id), None)
        if not target:
            raise ValueError(f"Node '{node_id}' not found.")

        # Identify incoming and outgoing edges for this node
        in_edges = [e for e in cloned.edges if e.target == node_id]
        out_edges = [e for e in cloned.edges if e.source == node_id]

        # Filter out all attached edges and the node itself
        cloned.nodes = [n for n in cloned.nodes if n.id != node_id]
        cloned.edges = [e for e in cloned.edges if e.source != node_id and e.target != node_id]

        # Reconnect upstream to downstream if requested
        if reconnect and in_edges and out_edges:
            for ie in in_edges:
                for oe in out_edges:
                    bridge_edge_id = f"edge_reconnect_{ie.source}_{oe.target}_{uuid.uuid4().hex[:4]}"
                    cloned.edges.append(
                        WorkflowEdgeSchema(
                            id=bridge_edge_id,
                            source=ie.source,
                            target=oe.target,
                            sourceHandle=ie.sourceHandle,
                            targetHandle=oe.targetHandle,
                        )
                    )

        cloned.version = increment_version(cloned.version, bump=bump_version)
        self.validate_modification(cloned)
        return cloned

    def add_edge(
        self,
        workflow: WorkflowBase,
        edge: Union[WorkflowEdgeSchema, Dict[str, Any]],
        bump_version: Literal["major", "minor", "patch"] = "patch",
    ) -> WorkflowBase:
        """Add an edge between existing nodes."""
        cloned = copy.deepcopy(workflow)
        new_edge = WorkflowEdgeSchema(**edge) if isinstance(edge, dict) else copy.deepcopy(edge)

        # Verify source and target exist
        node_ids = {n.id for n in cloned.nodes}
        if new_edge.source not in node_ids:
            raise ValueError(f"Source node '{new_edge.source}' does not exist.")
        if new_edge.target not in node_ids:
            raise ValueError(f"Target node '{new_edge.target}' does not exist.")

        # Prevent exact duplicate edges
        if any(e.source == new_edge.source and e.target == new_edge.target and e.condition == new_edge.condition for e in cloned.edges):
            return cloned

        cloned.edges.append(new_edge)
        cloned.version = increment_version(cloned.version, bump=bump_version)
        self.validate_modification(cloned)
        return cloned

    def remove_edge(
        self,
        workflow: WorkflowBase,
        edge_id: str,
        bump_version: Literal["major", "minor", "patch"] = "patch",
    ) -> WorkflowBase:
        """Remove an edge by ID."""
        cloned = copy.deepcopy(workflow)
        original_count = len(cloned.edges)
        cloned.edges = [e for e in cloned.edges if e.id != edge_id]

        if len(cloned.edges) == original_count:
            raise ValueError(f"Edge '{edge_id}' not found.")

        cloned.version = increment_version(cloned.version, bump=bump_version)
        self.validate_modification(cloned)
        return cloned

    def apply_patch(
        self,
        workflow: WorkflowBase,
        patch: Dict[str, Any],
    ) -> Tuple[WorkflowBase, WorkflowDiff]:
        """
        Apply a structured self-repair or modification patch dictionary:
        {
            "update_configs": [{"node_id": "...", "config": {...}}],
            "add_nodes": [...],
            "remove_nodes": ["node_id"],
            "add_edges": [...],
            "remove_edges": ["edge_id"],
            "bump_version": "patch"
        }
        Returns (new_workflow, workflow_diff).
        """
        orig_version = workflow.version
        current = copy.deepcopy(workflow)
        bump = patch.get("bump_version", "patch")

        for item in patch.get("update_configs", []):
            current = self.update_node_config(current, item["node_id"], item["config"], bump_version=bump)

        for item in patch.get("add_nodes", []):
            connect_after = item.get("connect_after")
            connect_before = item.get("connect_before")
            if "node" in item:
                node_spec = item["node"]
            else:
                node_spec = {k: v for k, v in item.items() if k not in ("connect_after", "connect_before")}
            current = self.add_node(current, node_spec, connect_after, connect_before, bump_version=bump)

        for node_id in patch.get("remove_nodes", []):
            current = self.remove_node(current, node_id, reconnect=patch.get("reconnect_removed", True), bump_version=bump)

        for edge in patch.get("add_edges", []):
            current = self.add_edge(current, edge, bump_version=bump)

        for edge_id in patch.get("remove_edges", []):
            current = self.remove_edge(current, edge_id, bump_version=bump)

        # Enforce atomic single-bump for the entire batch patch
        current.version = increment_version(orig_version, bump=bump)

        # Validate modified workflow before accepting it
        self.validate_modification(current)

        diff = compare_workflows(workflow, current)
        return current, diff


# Global singleton instance
workflow_modifier = WorkflowModifier()
