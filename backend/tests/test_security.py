import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from app.main import app


def test_api_key_protection_when_enabled(client: TestClient):
    """Verify that when REQUIRE_API_KEY is enabled, endpoints require valid X-API-Key."""
    # Temporarily enable API key requirement
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

