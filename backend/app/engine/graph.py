from collections import defaultdict, deque
from typing import Dict, Any, List, Set, Optional, Tuple
from app.engine.types import (
    WorkflowValidationError,
    CycleDetectedError,
)


def normalize_node(node: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes both canonical and React Flow (Member 3/Frontend) node payloads."""
    data = node.get("data") if isinstance(node.get("data"), dict) else {}
    raw_type = node.get("type")
    if not raw_type or raw_type == "customWorkflow":
        node_type = data.get("componentType") or raw_type or "Unknown"
    else:
        node_type = raw_type

    node_name = node.get("name") or data.get("label") or node.get("id", "")
    config = node.get("config")
    if not isinstance(config, dict) or not config:
        config = data.get("config") if isinstance(data.get("config"), dict) else {}

    return {
        **node,
        "type": node_type,
        "name": node_name,
        "config": config,
    }


class WorkflowGraph:
    """Interprets workflow graph topology, detects cycles, and determines execution order."""

    def __init__(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]):
        self.nodes = {n["id"]: normalize_node(n) for n in nodes if "id" in n}
        self.edges = edges
        self._validate_structure(nodes, edges)
        self.in_edges: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.out_edges: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._build_adjacency()

    def _validate_structure(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> None:
        if not nodes:
            raise WorkflowValidationError("Workflow must contain at least one node.")

        node_ids = set()
        for node in nodes:
            node_id = node.get("id")
            if not node_id:
                raise WorkflowValidationError("Every node in the workflow must have a valid 'id'.")
            if node_id in node_ids:
                raise WorkflowValidationError(f"Duplicate node id '{node_id}' found in workflow.")
            node_ids.add(node_id)

        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if not source or not target:
                raise WorkflowValidationError(f"Edge '{edge.get('id', 'unknown')}' missing source or target.")
            if source not in self.nodes:
                raise WorkflowValidationError(
                    f"Edge source '{source}' does not exist in workflow nodes."
                )
            if target not in self.nodes:
                raise WorkflowValidationError(
                    f"Edge target '{target}' does not exist in workflow nodes."
                )

    def _build_adjacency(self) -> None:
        for edge in self.edges:
            src = edge["source"]
            tgt = edge["target"]
            self.out_edges[src].append(edge)
            self.in_edges[tgt].append(edge)

    def get_topological_order(self) -> List[str]:
        """Kahn's algorithm for topological sorting and cycle detection."""
        in_degree: Dict[str, int] = {node_id: 0 for node_id in self.nodes}
        for edge in self.edges:
            in_degree[edge["target"]] += 1

        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        order = []

        while queue:
            node_id = queue.popleft()
            order.append(node_id)

            for edge in self.out_edges[node_id]:
                target = edge["target"]
                in_degree[target] -= 1
                if in_degree[target] == 0:
                    queue.append(target)

        if len(order) < len(self.nodes):
            unprocessed = [nid for nid, deg in in_degree.items() if deg > 0]
            raise CycleDetectedError(
                f"Cyclic workflow dependencies detected. Involved nodes: {unprocessed}"
            )

        return order

    def get_incoming_data(
        self,
        node_id: str,
        node_outputs: Dict[str, Any],
        skipped_nodes: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """Maps output data from active (non-skipped) upstream nodes to the current node's input payload."""
        incoming = self.in_edges.get(node_id, [])
        combined: Dict[str, Any] = {}
        skipped = skipped_nodes or set()

        for edge in incoming:
            src = edge["source"]
            if src in skipped or src not in node_outputs:
                continue

            source_output = node_outputs[src]
            source_handle = edge.get("sourceHandle")
            target_handle = edge.get("targetHandle")

            if source_handle and isinstance(source_output, dict) and source_handle in source_output:
                val = source_output[source_handle]
            else:
                val = source_output

            if target_handle:
                combined[target_handle] = val
                if isinstance(val, dict):
                    for k, v in val.items():
                        if k not in combined:
                            combined[k] = v
                elif "output" not in combined and target_handle in ("input", "prompt", "context", "params"):
                    combined["output"] = val
            elif isinstance(val, dict):
                for k, v in val.items():
                    if k not in combined:
                        combined[k] = v
                combined[src] = val
            else:
                combined[src] = val
                if "input" not in combined:
                    combined["input"] = val
                if "output" not in combined:
                    combined["output"] = val

        return combined

    def determine_skipped_nodes_for_condition(
        self,
        condition_node_id: str,
        taken_branch: str,
        existing_skipped: Optional[Set[str]] = None,
        untaken_edges_registry: Optional[Set[Tuple[str, str, Optional[str]]]] = None,
    ) -> Set[str]:
        """Identifies downstream nodes that must be SKIPPED because an untaken branch was chosen.

        Properly preserves join (diamond) nodes that remain reachable via at least one active/taken edge.
        """
        untaken_keys: Set[Tuple[str, str, Optional[str]]] = set(untaken_edges_registry or set())
        for edge in self.out_edges.get(condition_node_id, []):
            edge_branch = edge.get("sourceHandle") or edge.get("condition")
            if edge_branch is not None and str(edge_branch).lower() != str(taken_branch).lower():
                edge_key = (edge["source"], edge["target"], edge.get("id"))
                untaken_keys.add(edge_key)
                if untaken_edges_registry is not None:
                    untaken_edges_registry.add(edge_key)

        skipped: Set[str] = set(existing_skipped or set())
        topo_order = self.get_topological_order()
        cond_idx = topo_order.index(condition_node_id)

        for node_id in topo_order[cond_idx + 1 :]:
            if node_id in skipped:
                continue
            in_edges = self.in_edges.get(node_id, [])
            if not in_edges:
                continue

            all_incoming_inactive = True
            for edge in in_edges:
                edge_key = (edge["source"], edge["target"], edge.get("id"))
                if edge_key not in untaken_keys and edge["source"] not in skipped:
                    all_incoming_inactive = False
                    break

            if all_incoming_inactive:
                skipped.add(node_id)

        return skipped
