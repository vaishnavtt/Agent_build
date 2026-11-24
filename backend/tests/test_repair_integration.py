from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.repair.diagnosis import DiagnosticCode
from app.services.repair.integration import Availability, Dependency, RepairService
from app.services.repair.recovery_contracts import AttemptReservation
from examples.member6_demo import DemoTeam, run_demo


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def team(monkeypatch):
    fixture = DemoTeam()
    monkeypatch.setattr(app.state, "repair_service", RepairService(fixture.bindings()), raising=False)
    return fixture


def test_default_readiness_and_recovery_require_team_adapters(client):
    report = client.get("/api/v1/repair/readiness")
    assert report.status_code == 200
    assert report.headers["cache-control"] == "no-store"
    data = report.json()
    assert not data["recovery_available"]
    assert not data["diagnosis_available"]
    assert data["max_attempts"] == 2
    assert "attempt_reservation" in data["blockers"]
    for endpoint in ("diagnose", "recover"):
        result = client.post(f"/api/v1/repair/{endpoint}", json=DemoTeam().scope.model_dump())
        assert result.status_code == 503
        assert result.json()["status"] == "dependencies_unavailable"
        assert result.json()["attempts"] == []


@pytest.mark.parametrize(
    "availability",
    [Availability.UNAVAILABLE, Availability.INCOMPATIBLE, Availability.HUMAN_INTERVENTION],
)
def test_readiness_reports_adapter_status_and_standalone_diagnosis(client, team, monkeypatch, availability):
    bindings = replace(
        team.bindings(), attempts=None,
        availability={Dependency.CANDIDATE_EXECUTION: availability},
    )
    monkeypatch.setattr(app.state, "repair_service", RepairService(bindings))
    result = client.get("/api/v1/repair/readiness").json()
    assert result["diagnosis_available"]
    assert not result["recovery_available"]
    assert result["dependencies"]["candidate_execution"] == availability
    assert result["dependencies"]["attempt_reservation"] == "not_configured"
    diagnose = client.post("/api/v1/repair/diagnose", json=team.scope.model_dump())
    assert diagnose.status_code == 200
    assert diagnose.json()["diagnosis"]["affected_node_id"] == "output"
    assert not team.claimed


@pytest.mark.parametrize("key", ["verification", "repair_policy", "replacement", "failure_information"])
def test_api_rejects_untrusted_extra_fields_without_echoing_them(client, team, key):
    response = client.post(
        "/api/v1/repair/recover", json={**team.scope.model_dump(), key: "synthetic-private-marker"}
    )
    assert response.status_code == 422
    assert response.json()["status"] == "invalid_request"
    assert "synthetic-private-marker" not in response.text
    assert not team.claimed


@pytest.mark.parametrize("payload", [{"workflow_id": "only-workflow"}, {"workflow_id": ""}])
def test_api_requires_three_nonempty_identifiers(client, payload):
    response = client.post("/api/v1/repair/diagnose", json=payload)
    assert response.status_code == 422


def test_authorization_precedes_failure_lookup(client, team, monkeypatch):
    monkeypatch.setattr(team, "allows", lambda *_: False)
    monkeypatch.setattr(team, "get_failure", lambda *_: pytest.fail("Unauthorized lookup"))
    response = client.post("/api/v1/repair/diagnose", json=team.scope.model_dump())
    assert response.status_code == 403
    assert not team.claimed


@pytest.mark.parametrize("invalid", ["revision", "context", "missing"])
def test_server_evidence_must_match_scope(client, team, monkeypatch, invalid):
    if invalid == "missing":
        monkeypatch.setattr(team, "get_failure", lambda *_: None)
    elif invalid == "revision":
        team.failure = team.failure.model_copy(update={"workflow_revision_id": "stale"})
    else:
        team.context = replace(team.context, execution_run_id="different")
    response = client.post("/api/v1/repair/recover", json=team.scope.model_dump())
    assert response.status_code == (404 if invalid == "missing" else 409)
    assert not team.claimed


def test_production_api_requires_durable_claim_before_recovery(client, team, monkeypatch):
    monkeypatch.setattr(team, "begin", lambda *_: AttemptReservation.UNAVAILABLE)
    response = client.post("/api/v1/repair/recover", json=team.scope.model_dump())
    assert response.status_code == 503
    assert not team.candidates


@pytest.mark.parametrize(
    ("decision", "status", "http"),
    [
        (AttemptReservation.LIMIT_REACHED, "attempt_limit_reached", 409),
        (AttemptReservation.CONFLICT, "attempt_reservation_blocked", 503),
    ],
)
def test_reservation_must_succeed_before_candidate_application(client, team, monkeypatch, decision, status, http):
    monkeypatch.setattr(team, "reserve", lambda *_, **__: decision)
    response = client.post("/api/v1/repair/recover", json=team.scope.model_dump())
    assert response.status_code == http
    assert response.json()["status"] == status
    assert response.json()["attempts"] == []
    assert not team.candidates


def test_recover_promotes_verified_candidate_and_rejects_duplicate(client, team, monkeypatch):
    verify = team.verify

    def verify_after_reservation(candidate, baseline):
        assert team.reserved == [1]
        return verify(candidate, baseline)

    monkeypatch.setattr(team, "verify", verify_after_reservation)
    body = team.scope.model_dump()
    first = client.post("/api/v1/repair/recover", json=body)
    assert first.status_code == 200
    report = first.json()
    assert report["status"] == "promoted"
    assert report["promotion"] == "confirmed"
    attempt, = report["attempts"]
    assert attempt["verification_status"] == "passed"
    assert attempt["candidate"]["revision_id"] == attempt["verification"]["candidate_revision_id"]
    assert "proposed_value" not in attempt["proposal"]
    assert "graph_json" not in first.text
    assert team.finished is not None
    repeated = client.post("/api/v1/repair/recover", json=body)
    assert repeated.status_code == 409
    assert repeated.json()["status"] == "duplicate_request"
    assert len(team.candidates) == 1


def test_server_input_failure_is_sanitized(client, team, monkeypatch):
    def fail(*_):
        raise RuntimeError("synthetic-secret-from-dependency")

    monkeypatch.setattr(team, "get_failure", fail)
    response = client.post("/api/v1/repair/diagnose", json=team.scope.model_dump())
    assert response.status_code == 503
    assert "synthetic-secret-from-dependency" not in response.text


def test_human_review_is_available_without_mutating_workflow(client, team):
    team.failure = team.failure.model_copy(update={"error_code": DiagnosticCode.MISSING_API_CREDENTIALS})
    response = client.post("/api/v1/repair/diagnose", json=team.scope.model_dump())
    diagnosis = response.json()["diagnosis"]
    assert response.status_code == 200
    assert diagnosis["category"] == "credentials"
    assert diagnosis["requires_human_intervention"]
    assert not diagnosis["repairable"]
    assert team.active == team.original


def test_standalone_demo_covers_all_five_outcomes():
    report = run_demo()
    assert [item["status"] for item in report.values()] == [
        "promoted", "human_review", "rolled_back", "dependencies_unavailable", "revision_conflict",
    ]
    assert [item["attempts"] for item in report.values()] == [1, 0, 1, 0, 0]
