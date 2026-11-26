"""
AgentForge AI - Workflow Version Compatibility & Change Tracking (Member 3)
Provides semver versioning helpers, workflow comparison/diffing,
and change tracking structures between workflow revisions.
"""

import copy
import re
from typing import Dict, List, Any, Optional, Tuple, Literal
from pydantic import BaseModel, Field, computed_field

from app.schemas.workflow import (
    WorkflowBase,
    WorkflowNodeSchema,
    WorkflowEdgeSchema,
    WorkflowConfigurationSchema,
)


class NodeDiff(BaseModel):
    """Detailed diff for a specific modified node."""
    node_id: str
    node_name: str
    component_type: str
    field_changes: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Map of field name to {'before': old_val, 'after': new_val}"
    )
    config_changes: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Map of config key to {'before': old_val, 'after': new_val}"
    )


class EdgeDiff(BaseModel):
    """Detailed diff for a modified edge."""
    edge_id: str
    before: Dict[str, Any]
    after: Dict[str, Any]
    changes: Dict[str, Dict[str, Any]]


class WorkflowDiff(BaseModel):
    """Structured report comparing two workflow revisions."""
    version_from: str
    version_to: str
    workflow_name: str

    added_nodes: List[WorkflowNodeSchema] = Field(default_factory=list)
    removed_nodes: List[WorkflowNodeSchema] = Field(default_factory=list)
    modified_nodes: List[NodeDiff] = Field(default_factory=list)

    added_edges: List[WorkflowEdgeSchema] = Field(default_factory=list)
    removed_edges: List[WorkflowEdgeSchema] = Field(default_factory=list)
    modified_edges: List[EdgeDiff] = Field(default_factory=list)

    configuration_changes: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    metadata_changes: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    is_compatible: bool = True
    summary: str = ""

    @computed_field
    def has_changes(self) -> bool:
        return bool(
            self.added_nodes
            or self.removed_nodes
            or self.modified_nodes
            or self.added_edges
            or self.removed_edges
            or self.modified_edges
            or self.configuration_changes
            or self.metadata_changes
        )


def increment_version(
    current_version: str,
    bump: Literal["major", "minor", "patch"] = "minor"
) -> str:
    """
    Increment semantic version string (e.g. 1.0.0 -> 1.1.0 or 1.0.1 or 2.0.0).
    """
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", current_version.strip())
    if not match:
        # Default fallback
        return "1.1.0"

    major, minor, patch = map(int, match.groups())
    if bump == "major":
        return f"{major + 1}.0.0"
    elif bump == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def compare_workflows(
    v1: WorkflowBase,
    v2: WorkflowBase
) -> WorkflowDiff:
    """
    Compare two workflow objects and compute an explicit change diff.
    """
    v1_nodes = {n.id: n for n in (v1.nodes or [])}
    v2_nodes = {n.id: n for n in (v2.nodes or [])}

    v1_edges = {e.id: e for e in (v1.edges or [])}
    v2_edges = {e.id: e for e in (v2.edges or [])}

    added_nodes = sorted(
        [v2_nodes[nid] for nid in v2_nodes if nid not in v1_nodes],
        key=lambda n: n.id,
    )
    removed_nodes = sorted(
        [v1_nodes[nid] for nid in v1_nodes if nid not in v2_nodes],
        key=lambda n: n.id,
    )
    modified_nodes: List[NodeDiff] = []

    # Check shared nodes for modifications in deterministic order
    for nid in sorted(v1_nodes.keys()):
        if nid in v2_nodes:
            n1 = v1_nodes[nid]
            n2 = v2_nodes[nid]

            field_changes: Dict[str, Dict[str, Any]] = {}
            if n1.name != n2.name:
                field_changes["name"] = {"before": n1.name, "after": n2.name}
            if n1.type != n2.type:
                field_changes["type"] = {"before": n1.type, "after": n2.type}
            if n1.inputHandles != n2.inputHandles:
                field_changes["inputHandles"] = {"before": n1.inputHandles, "after": n2.inputHandles}
            if n1.outputHandles != n2.outputHandles:
                field_changes["outputHandles"] = {"before": n1.outputHandles, "after": n2.outputHandles}
            if n1.position.x != n2.position.x or n1.position.y != n2.position.y:
                field_changes["position"] = {
                    "before": {"x": n1.position.x, "y": n1.position.y},
                    "after": {"x": n2.position.x, "y": n2.position.y},
                }

            # Check config dictionary diff
            config_changes: Dict[str, Dict[str, Any]] = {}
            c1 = n1.config or {}
            c2 = n2.config or {}
            all_keys = set(c1.keys()).union(c2.keys())
            for k in all_keys:
                if c1.get(k) != c2.get(k):
                    config_changes[k] = {"before": c1.get(k), "after": c2.get(k)}

            if field_changes or config_changes:
                modified_nodes.append(
                    NodeDiff(
                        node_id=nid,
                        node_name=n2.name,
                        component_type=n2.type,
                        field_changes=field_changes,
                        config_changes=config_changes,
                    )
                )

    # Edge diffs
    added_edges = sorted(
        [v2_edges[eid] for eid in v2_edges if eid not in v1_edges],
        key=lambda e: e.id,
    )
    removed_edges = sorted(
        [v1_edges[eid] for eid in v1_edges if eid not in v2_edges],
        key=lambda e: e.id,
    )
    modified_edges: List[EdgeDiff] = []

    for eid in sorted(v1_edges.keys()):
        if eid in v2_edges:
            e1 = v1_edges[eid]
            e2 = v2_edges[eid]
            edge_changes: Dict[str, Dict[str, Any]] = {}

            if e1.source != e2.source:
                edge_changes["source"] = {"before": e1.source, "after": e2.source}
            if e1.target != e2.target:
                edge_changes["target"] = {"before": e1.target, "after": e2.target}
            if e1.sourceHandle != e2.sourceHandle:
                edge_changes["sourceHandle"] = {"before": e1.sourceHandle, "after": e2.sourceHandle}
            if e1.targetHandle != e2.targetHandle:
                edge_changes["targetHandle"] = {"before": e1.targetHandle, "after": e2.targetHandle}
            if e1.condition != e2.condition:
                edge_changes["condition"] = {"before": e1.condition, "after": e2.condition}

            if edge_changes:
                modified_edges.append(
                    EdgeDiff(
                        edge_id=eid,
                        before=e1.model_dump(),
                        after=e2.model_dump(),
                        changes=edge_changes,
                    )
                )

    # Configuration changes
    config_changes: Dict[str, Dict[str, Any]] = {}
    cfg1 = v1.configuration.model_dump() if v1.configuration else {}
    cfg2 = v2.configuration.model_dump() if v2.configuration else {}
    for k in set(cfg1.keys()).union(cfg2.keys()):
        if cfg1.get(k) != cfg2.get(k):
            config_changes[k] = {"before": cfg1.get(k), "after": cfg2.get(k)}

    # Metadata changes
    metadata_changes: Dict[str, Dict[str, Any]] = {}
    if v1.name != v2.name:
        metadata_changes["name"] = {"before": v1.name, "after": v2.name}
    if v1.description != v2.description:
        metadata_changes["description"] = {"before": v1.description, "after": v2.description}
    if v1.tags != v2.tags:
        metadata_changes["tags"] = {"before": v1.tags, "after": v2.tags}

    # Backward compatibility heuristic:
    # If Input node handles or Output node handles were removed, or required inputs altered, it may break callers.
    is_compatible = True
    v1_input_nodes = [n for n in v1.nodes if n.type == "Input"]
    v2_input_nodes = [n for n in v2.nodes if n.type == "Input"]
    if len(v1_input_nodes) > 0 and len(v2_input_nodes) == 0:
        is_compatible = False
    if len(removed_nodes) > 0 and any(n.type in ("Input", "Output") for n in removed_nodes):
        is_compatible = False

    # Human-readable summary
    summary_parts = []
    if added_nodes:
        summary_parts.append(f"+{len(added_nodes)} node(s)")
    if removed_nodes:
        summary_parts.append(f"-{len(removed_nodes)} node(s)")
    if modified_nodes:
        summary_parts.append(f"~{len(modified_nodes)} modified node(s)")
    if added_edges:
        summary_parts.append(f"+{len(added_edges)} edge(s)")
    if removed_edges:
        summary_parts.append(f"-{len(removed_edges)} edge(s)")
    if modified_edges:
        summary_parts.append(f"~{len(modified_edges)} modified edge(s)")

    summary = ", ".join(summary_parts) if summary_parts else "No structural changes."

    return WorkflowDiff(
        version_from=v1.version,
        version_to=v2.version,
        workflow_name=v2.name,
        added_nodes=added_nodes,
        removed_nodes=removed_nodes,
        modified_nodes=modified_nodes,
        added_edges=added_edges,
        removed_edges=removed_edges,
        modified_edges=modified_edges,
        configuration_changes=config_changes,
        metadata_changes=metadata_changes,
        is_compatible=is_compatible,
        summary=summary,
    )


def restore_version(target_workflow: WorkflowBase) -> WorkflowBase:
    """
    Restores an earlier saved workflow version as an independent copy.
    Guarantees that all node IDs, connections, and configurations are preserved,
    and that no existing workflow objects are mutated.
    """
    return copy.deepcopy(target_workflow)


def rollback_to_version(
    current_workflow: WorkflowBase,
    target_version_workflow: WorkflowBase,
    bump: Literal["major", "minor", "patch"] = "minor",
) -> Tuple[WorkflowBase, WorkflowDiff]:
    """
    Rolls back the current workflow to the state of an earlier saved version.
    Restores all node IDs, connections, and configurations from the target version,
    advances the semantic version to document the rollback, and computes the diff.
    """
    restored = copy.deepcopy(target_version_workflow)
    new_version = increment_version(current_workflow.version, bump=bump)
    restored.version = new_version

    diff = compare_workflows(current_workflow, restored)
    diff.summary = f"Rollback to version {target_version_workflow.version} (promoted as v{new_version})"

    return restored, diff


class WorkflowHistory:
    """
    Version-safe history repository supporting version registration, retrieval,
    and non-destructive rollback.
    """

    def __init__(self):
        self._history: Dict[str, WorkflowBase] = {}

    def save_version(self, workflow: WorkflowBase, allow_overwrite: bool = False) -> str:
        """
        Save an immutable snapshot of a workflow version.
        Guards against accidental overwriting of previous snapshots.
        """
        if workflow.version in self._history and not allow_overwrite:
            raise ValueError(
                f"Version '{workflow.version}' already exists in history. Versions are immutable snapshots and cannot be overwritten."
            )
        self._history[workflow.version] = copy.deepcopy(workflow)
        return workflow.version

    def get_version(self, version: str) -> Optional[WorkflowBase]:
        """Fetch an immutable copy of a saved version."""
        wf = self._history.get(version)
        return copy.deepcopy(wf) if wf else None

    def list_versions(self) -> List[str]:
        """List all saved version strings."""
        return list(self._history.keys())

    def rollback(
        self,
        target_version: str,
        current_workflow: Optional[WorkflowBase] = None,
        bump: Literal["major", "minor", "patch"] = "minor",
    ) -> Tuple[WorkflowBase, WorkflowDiff]:
        """
        Roll back current workflow (or latest saved version) to a saved target_version from history.
        The new rolled-back workflow is registered into history and returned alongside its diff.
        """
        target = self.get_version(target_version)
        if not target:
            raise ValueError(f"Version '{target_version}' not found in workflow history.")

        if current_workflow is None:
            if not self._history:
                raise ValueError("No versions available in history to rollback from.")
            latest_ver = list(self._history.keys())[-1]
            current_workflow = self._history[latest_ver]

        rolled_back, diff = rollback_to_version(current_workflow, target, bump=bump)
        self.save_version(rolled_back)
        return rolled_back, diff
