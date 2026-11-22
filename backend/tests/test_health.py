import pytest
from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient):
    """Verify GET /api/v1/health returns 200 OK and valid health schema."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "AgentForge AI"
    assert data["version"] == "1.0.0"
    assert data["database"] == "connected"
    assert "timestamp" in data
    assert data["details"]["supported_nodes_count"] == 7


def test_root_redirects_to_docs(client: TestClient):
    """Verify GET / redirects to /docs."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/docs"
