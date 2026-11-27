import logging
import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from app.core.logging import SensitiveDataFilter
from app.main import app


def test_api_key_protection_when_enabled(client: TestClient):
    """Verify that when REQUIRE_API_KEY is enabled, endpoints require valid X-API-Key."""
    original_require = settings.REQUIRE_API_KEY
    original_key = settings.API_KEY

    try:
        settings.REQUIRE_API_KEY = True
        settings.API_KEY = "test-secret-agentforge-key-2026"

        # 1. Request without key -> 401 Unauthorized
        res_no_key = client.get("/api/v1/workflows")
        assert res_no_key.status_code == 401
        assert "api key" in res_no_key.json()["detail"].lower()

        # 2. Request with invalid key -> 401 Unauthorized
        res_bad_key = client.get("/api/v1/workflows", headers={"X-API-Key": "wrong-key"})
        assert res_bad_key.status_code == 401

        # 3. Request with valid key -> 200 OK
        res_good_key = client.get(
            "/api/v1/workflows",
            headers={"X-API-Key": "test-secret-agentforge-key-2026"},
        )
        assert res_good_key.status_code == 200

    finally:
        settings.REQUIRE_API_KEY = original_require
        settings.API_KEY = original_key


def test_workflow_ownership_authorization(client: TestClient):
    """Verify that users cannot modify or delete workflows owned by other principals (403 Forbidden)."""
    alice_headers = {"X-Principal-ID": "alice"}
    bob_headers = {"X-Principal-ID": "bob"}

    # 1. Alice creates a workflow
    res = client.post(
        "/api/v1/workflows",
        json={"name": "Alice Workflow", "nodes": [], "edges": []},
        headers=alice_headers,
    )
    assert res.status_code == 201
    wf_id = res.json()["id"]
    assert res.json()["owner_id"] == "alice"

    # 2. Bob attempts to modify Alice's workflow -> 403 Forbidden
    res_bob_update = client.put(
        f"/api/v1/workflows/{wf_id}",
        json={"name": "Bob Hijack Attempt"},
        headers=bob_headers,
    )
    assert res_bob_update.status_code == 403
    assert "access denied" in res_bob_update.json()["detail"].lower()

    # 3. Bob attempts to delete Alice's workflow -> 403 Forbidden
    res_bob_delete = client.delete(
        f"/api/v1/workflows/{wf_id}",
        headers=bob_headers,
    )
    assert res_bob_delete.status_code == 403

    # 4. Alice can update her own workflow -> 200 OK
    res_alice_update = client.put(
        f"/api/v1/workflows/{wf_id}",
        json={"name": "Alice Legitimate Update"},
        headers=alice_headers,
    )
    assert res_alice_update.status_code == 200
    assert res_alice_update.json()["name"] == "Alice Legitimate Update"

    # 5. Alice can delete her own workflow -> 204 No Content
    res_alice_delete = client.delete(
        f"/api/v1/workflows/{wf_id}",
        headers=alice_headers,
    )
    assert res_alice_delete.status_code == 204


def test_sql_parameter_log_redaction():
    """Verify that SensitiveDataFilter masks sensitive SQL queries, tokens, and API keys."""
    log_filter = SensitiveDataFilter()

    # Test record containing API key and token in message string
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Executing query: SELECT * FROM users WHERE api_key='secret-key-1234' AND token='jwt-xyz'",
        args=(),
        exc_info=None,
    )

    # Apply filter
    log_filter.filter(record)

    # Check that secrets are replaced with REDACTED
    assert "secret-key-1234" not in record.msg
    assert "jwt-xyz" not in record.msg
    assert "REDACTED" in record.msg
