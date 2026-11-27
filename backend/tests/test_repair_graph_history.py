"""Member 6 contract tests. GraphDemo is an explicitly in-memory team fixture."""
from dataclasses import replace
import json
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.v1.endpoints.repair import router
from app.services.repair.graph_policy import GraphPermit, apply, fingerprint, prepare
from app.services.repair.history import HistoryPage, StoredRecovery
from app.services.repair.integration import RepairBindings, RepairService
from app.services.repair.recovery_contracts import AttemptStatus, RevisionConflict
from app.services.repair.structural import Member5StructuralValidation
from tests.test_repair_recovery_graph import FixtureVerifier
from examples.member6_demo import GraphDemo, graph_demo


@pytest.fixture
def team():
    return GraphDemo()


def plan(team):
    return prepare(team, team.failure, "transfer", team.original)


@pytest.mark.parametrize("missing", [True, False])
def test_isolated_exact_restoration(missing):
    team = GraphDemo(missing=missing)
    before = team.original.graph_json
    proposal = plan(team)
    graph = apply(team, proposal, team.failure, "transfer", team.original)
    assert graph == json.loads(team.last_working.graph_json)
    original = json.loads(before)
    assert {**graph, "edges": original["edges"]} == original
    assert proposal.candidate_digest == fingerprint(graph)
    graph["nodes"].clear()
    assert team.original.graph_json == before


@pytest.mark.parametrize("field,value", [
    ("fingerprint", "0" * 64), ("source_revision_id", "other"), ("workflow_id", "other"),
    ("workflow_revision_id", "other"), ("execution_run_id", "other"), ("failed_node_id", "input"),
    ("target_type", "number"), ("edge_id", "other"), ("schema_id", "unapproved"),
    ("classification", "private"), ("operation", "patch"),
])
def test_reject_changed_authority(team, field, value):
    team.permission = team.permission.model_copy(update={field: value})
    with pytest.raises(ValueError):
        plan(team)


@pytest.mark.parametrize("defect", ["unknown_node", "unknown_handle", "duplicate_edge", "ambiguous_mapping",
                                    "protected", "approval", "condition", "cycle", "additional_edit", "stale_mapping",
                                    "different_edge", "tool"])
def test_reject_unsafe_graph(team, defect):
    graph = json.loads(team.original.graph_json)
    working = json.loads(team.last_working.graph_json)
    match defect:
        case "unknown_node": graph["nodes"][0]["id"] = "unknown"
        case "unknown_handle": graph["nodes"][0]["outputHandles"] = ["other"]
        case "duplicate_edge": graph["edges"] *= 2
        case "ambiguous_mapping": graph["nodes"][1]["inputHandles"].append("another")
        case "protected": working["testCriteria"] = []
        case "approval": working["nodes"].append({"id": "gate", "type": "Human Approval"})
        case "condition": working["edges"][0]["condition"] = "approved"
        case "cycle": working["edges"][0]["target"] = "input"
        case "additional_edit": working["requirements"] = ["other"]
        case "stale_mapping": graph["edges"][0]["sourceHandle"] = "another"
        case "different_edge": graph["edges"][0]["id"] = "different"
        case "tool": graph["nodes"][0]["type"] = "Tool"
    team.original = replace(team.original, graph_json=json.dumps(graph))
    team.last_working = replace(team.last_working, graph_json=json.dumps(working))
    team.permission = team.permission.model_copy(update={"fingerprint": fingerprint(graph)})
    with pytest.raises(ValueError):
        plan(team)


def test_arbitrary_patch_rejected(team):
    with pytest.raises(ValidationError):
        GraphPermit(**team.permission.model_dump(), patch=[{"op": "replace"}])


def test_compiled_graph_demo():
    results = graph_demo()
    assert results["mapping"] == results["missing_connection"] == "promoted"
    assert results["unapproved_connection"] == "human_review"


def test_denied_graph_permit_requires_review_without_reserving(team):
    team.permission = None
    code, result = RepairService(team.bindings()).run(team.scope, Request({"type": "http"}), "recover")
    assert code == 200 and result.status == "human_review"
    assert not team.reserved and team.active == team.original


def test_recheck_after_reservation(team):
    reserve = team.reserve
    def changed(scope, number, *, limit):
        decision = reserve(scope, number, limit=limit)
        team.permission = None
        return decision
    team.reserve = changed
    _, result = RepairService(team.bindings()).run(team.scope, Request({"type": "http"}), "recover")
    assert result.status == "application_failed" and len(result.attempts) == 1
    assert team.active == team.original


@pytest.mark.parametrize("check", ["structural", "execution", "failed_test", "regression"])
def test_mapping_failed_verification_cannot_promote(team, check):
    # This existing verifier fixture uses test-1 and test-2 for its stage failure injection.
    team.failure = team.failure.model_copy(update={"failed_test_ids": ("test-1",)})
    verifier = FixtureVerifier(team.failure)
    verifier.check = check
    service = RepairService(replace(team.bindings(), verifier=verifier))
    _, result = service.run(team.scope, Request({"type": "http"}), "recover")
    assert result.status == "rolled_back" and result.promotion is None and team.reserved == [1]
    assert result.retry_stop == "no_safe_alternative"
    assert service.history(team.scope, Request({"type":"http"}), 0, 5)[0] == 200


@pytest.mark.parametrize("valid,errors,outcome", [(True, [], "promoted"), (False, [1], "rolled_back"),
                                                   (True, [1], "verification_unavailable")])
def test_structural_bridge_gates_execution(team, valid, errors, outcome):
    class Validator:
        def validate(self, nodes, edges, workflow_id):
            return SimpleNamespace(workflow_id=workflow_id, total_nodes=len(nodes), total_connections=len(edges),
                                   is_valid=valid, errors=errors)
    if errors:
        team.verify = lambda *_: pytest.fail("Candidate execution started after structural rejection")
    service = RepairService(replace(team.bindings(), structural=Member5StructuralValidation(Validator())))
    _, result = service.run(team.scope, Request({"type":"http"}), "recover")
    assert result.status == outcome


def test_named_source_handle_and_absent_target_mapping(team):
    for source in (True, False):
        team = GraphDemo()
        graph = json.loads(team.last_working.graph_json)
        handle = "sourceHandle" if source else "targetHandle"
        graph["edges"][0].pop(handle)
        team.original = replace(team.original, graph_json=json.dumps(graph))
        node = "input" if source else "output"
        code = "INVALID_SOURCE_HANDLE" if source else "INVALID_TARGET_HANDLE"
        team.failure = team.failure.model_copy(update={"error_code":code, "failed_node_id":node})
        team.permission = team.permission.model_copy(update={"failed_node_id":node, "error_code":code,
            "fingerprint":fingerprint(graph), "operation":team.permission.operation})
        assert json.loads(plan(team).replacement_edge_json)[handle] == team.ports.model_dump()[handle]


def client(bindings):
    app = FastAPI()
    app.include_router(router)
    app.state.repair_service = RepairService(bindings)
    return TestClient(app)


def test_authorized_history_pagination_and_redaction(team):
    service = RepairService(team.bindings())
    service.run(team.scope, Request({"type": "http"}), "recover")
    outcome = replace(team.finished, explanation="private diagnostic text")
    team.read = lambda request, scope, offset, limit: HistoryPage(scope, tuple(
        StoredRecovery(str(n), outcome) for n in range(offset, min(3, offset + limit))))
    api = client(team.bindings())
    response = api.get("/history", params={**team.scope.model_dump(), "limit": 2})
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    data = response.json()
    assert data["next_offset"] == 2 and len(data["records"]) == 2
    assert data["records"][0]["status"] == "promoted"
    assert data["records"][0]["duration_ms"] is None
    assert "private diagnostic" not in response.text and "replacement_edge_json" not in response.text
    assert len(api.get("/history", params={**data["scope"], "offset": 2}).json()["records"]) == 1


@pytest.mark.parametrize("condition,expected", [("denied",403), ("unknown_run",404), ("unknown_workflow",404),
    ("stale",409), ("wrong_scope",503), ("wrong_result",503), ("false_success",503), ("inconsistent_attempt",503), ("absent",503),
    ("empty",200), ("read_denied",403), ("error",503)])
def test_history_failure_states(team, condition, expected):
    bindings = team.bindings()
    def read(request, scope, offset, limit):
        if condition.startswith("unknown"): return None
        if condition == "stale": raise RevisionConflict()
        if condition == "read_denied": raise PermissionError()
        if condition == "error": raise RuntimeError("private detail")
        if condition == "wrong_scope": return HistoryPage(scope.model_copy(update={"execution_run_id":"other"}), ())
        if condition in ("wrong_result", "false_success", "inconsistent_attempt"):
            RepairService(bindings).run(scope, request, "recover")
            if condition == "wrong_result":
                change = {"execution_run_id": "other"}
            elif condition == "false_success":
                change = {"attempts": ()}
            else:
                attempt, = team.finished.attempts
                change = {"attempts": (replace(attempt, status=AttemptStatus.VERIFICATION_FAILED),)}
            return HistoryPage(scope, (StoredRecovery("r", replace(team.finished, **change)),))
        return HistoryPage(scope, ())
    team.read = read
    if condition == "denied": team.allows = lambda *args: False
    if condition == "absent": bindings = RepairBindings()
    response = client(bindings).get("/history", params=team.scope.model_dump())
    assert response.status_code == expected and "private detail" not in response.text
    if condition == "empty": assert response.json()["records"] == []
