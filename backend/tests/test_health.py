from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_liveness_does_not_require_dependencies() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_returns_200_when_dependencies_are_ready(monkeypatch) -> None:
    async def ready() -> dict[str, object]:
        return {
            "status": "ready",
            "dependencies": {
                "database": {"status": "ok"},
                "redis": {"status": "ok"},
            },
        }

    monkeypatch.setattr("app.main.readiness_status", ready)

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_returns_503_when_dependency_is_unavailable(monkeypatch) -> None:
    async def not_ready() -> dict[str, object]:
        return {
            "status": "not_ready",
            "dependencies": {
                "database": {"status": "error", "error": "ConnectionError"},
                "redis": {"status": "ok"},
            },
        }

    monkeypatch.setattr("app.main.readiness_status", not_ready)

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


def test_health_preserves_readiness_semantics(monkeypatch) -> None:
    async def not_ready() -> dict[str, object]:
        return {
            "status": "not_ready",
            "dependencies": {
                "database": {"status": "ok"},
                "redis": {"status": "error", "error": "ConnectionError"},
            },
        }

    monkeypatch.setattr("app.main.readiness_status", not_ready)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
