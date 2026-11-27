"""Restore a named, public data connection from an authenticated working snapshot."""
import json
import re
from enum import StrEnum
from hashlib import sha256
from typing import Literal, Protocol

from pydantic import Field

from app.schemas.repair import FailureInformation, Identifier, RepairContract
from app.services.repair.diagnosis import GRAPH_CODES
from app.services.repair.planning import UnsafeRepair
from app.services.repair.service import WorkflowSnapshot


class GraphOperation(StrEnum):
    CONNECTION = "restore_connection"
    MAPPING = "restore_mapping"


class PortPair(RepairContract):
    source: Identifier
    target: Identifier
    sourceHandle: Identifier
    targetHandle: Identifier


class GraphPermit(RepairContract):
    workflow_id: Identifier
    workflow_revision_id: Identifier
    execution_run_id: Identifier
    failed_node_id: Identifier
    error_code: Identifier
    edge_id: Identifier
    operation: GraphOperation
    policy_id: Identifier
    schema_id: Literal["member3-named-handles-v1"]
    fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_revision_id: Identifier
    ports: PortPair
    source_type: Literal["string", "number", "boolean"]
    target_type: Literal["string", "number", "boolean"]
    classification: Literal["public_data"]
    verification: Literal["structure_execution_failed_and_regression_tests"]


class GraphAuthority(Protocol):
    def permit(self, failure: FailureInformation, edge_id: str) -> GraphPermit | None:
        """Authenticate the schema, failure, safe ports, policy and exact revision digest."""
        ...

    def working_snapshot(self, permit: GraphPermit) -> WorkflowSnapshot | None:
        """Return the immutable verified revision from the authorized workflow."""
        ...


class GraphPlan(RepairContract):
    permit: GraphPermit
    original_edge_json: str | None = Field(repr=False)
    replacement_edge_json: str = Field(repr=False)
    candidate_digest: str


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value: object) -> str:
    return sha256(canonical(value).encode()).hexdigest()


def require(condition):
    if not condition:
        raise UnsafeRepair("Graph restoration preconditions are not satisfied.")


def read_graph(snapshot: WorkflowSnapshot) -> dict:
    def unique(items):
        result = dict(items)
        require(len(result) == len(items))
        return result
    return json.loads(snapshot.graph_json, object_pairs_hook=unique)


def prepare(authority: GraphAuthority, failure: FailureInformation, edge_id: str,
            snapshot: WorkflowSnapshot) -> GraphPlan:
    permit = authority.permit(failure, edge_id)
    require(isinstance(permit, GraphPermit))
    permit = GraphPermit.model_validate(permit.model_dump(warnings=False))
    require(all(getattr(permit, key) == getattr(failure, key) for key in
                ("workflow_id", "workflow_revision_id", "execution_run_id", "failed_node_id", "error_code")))
    require(permit.edge_id == edge_id and failure.error_code in GRAPH_CODES)
    require((snapshot.workflow_id, snapshot.revision_id) == (permit.workflow_id, permit.workflow_revision_id))
    working = authority.working_snapshot(permit)
    require(working and working.workflow_id == snapshot.workflow_id and
            working.revision_id == permit.source_revision_id != snapshot.revision_id)
    graph = read_graph(snapshot)
    prior = read_graph(working)
    require(fingerprint(graph) == permit.fingerprint and permit.source_type == permit.target_type)
    # Intentionally narrow: direct data transfer only. Additional executable nodes,
    # approvals, conditional paths and external actions need separate policies.
    nodes = graph["nodes"]
    ports = permit.ports
    require(len(nodes) == 2 and {node["id"] for node in nodes} == {ports.source, ports.target}
            and ports.source != ports.target and failure.failed_node_id in (ports.source, ports.target))
    if "configuration" in graph:
        require(graph["configuration"].get("autoRepairEnabled", True) is True)
    require(all(handle.isidentifier() and not any(word in re.sub(r"[^a-z0-9]", "", handle.lower()) for word in (
        "secret", "password", "token", "credential", "apikey", "private", "permission", "approval",
        "condition", "script", "command", "requirement", "criteria", "authorization",
    )) for handle in (ports.sourceHandle, ports.targetHandle)))
    source, = (node for node in nodes if node["id"] == ports.source)
    target, = (node for node in nodes if node["id"] == ports.target)
    require(all(set(node) <= {"id", "type", "config", "name", "position", "inputHandles", "outputHandles"}
                for node in nodes))
    require(source["type"] == "Input" and target["type"] == "Output")
    require(source.get("config", {}) in ({}, {"inputType": "text"}, {"inputType": "text", "required": True}))
    require(target.get("config", {}) in ({}, {"outputFormat": "text"}, {"outputFormat": "markdown"}))
    require(source.get("outputHandles") == [ports.sourceHandle] and target.get("inputHandles") == [ports.targetHandle])
    require(len(prior["edges"]) == 1)
    replacement = prior["edges"][0]
    require(replacement.get("id") == edge_id and replacement.get("condition") is None)
    require(set(replacement) <= {"id", "condition", *ports.model_dump()})
    require(all(replacement.get(key) == value for key, value in ports.model_dump().items()))
    edges = graph["edges"]
    require(isinstance(edges, list) and len(edges) <= 1)
    original = edges[0] if edges else None
    if original is None:
        require(edges == [] and permit.operation == GraphOperation.CONNECTION and failure.error_code == "NO_PATH_TO_OUTPUT"
                and permit.failed_node_id == ports.target)
    else:
        require(original["id"] == edge_id)
        handle = {"INVALID_SOURCE_HANDLE": "sourceHandle", "INVALID_TARGET_HANDLE": "targetHandle"}.get(failure.error_code)
        require(handle and failure.failed_node_id == (ports.source if handle == "sourceHandle" else ports.target))
        require(original.get(handle) != replacement[handle] and {**original, handle: replacement[handle]} == replacement)
    # Reverse the permitted difference on a detached read of the working revision.
    # No candidate exists until the coordinator reserves an attempt.
    candidate_digest = fingerprint(prior)
    prior["edges"] = edges
    require(canonical(prior) == canonical(graph))
    return GraphPlan(permit=permit, original_edge_json=canonical(original) if original else None,
                     replacement_edge_json=canonical(replacement), candidate_digest=candidate_digest)


def apply(authority: GraphAuthority, plan: GraphPlan, failure: FailureInformation,
          edge_id: str, snapshot: WorkflowSnapshot) -> dict:
    require(prepare(authority, failure, edge_id, snapshot) == plan)
    # Deserialization creates independent containers for every nested value.
    candidate = read_graph(snapshot)
    candidate["edges"] = [json.loads(plan.replacement_edge_json)]
    require(fingerprint(candidate) == plan.candidate_digest)
    return candidate
