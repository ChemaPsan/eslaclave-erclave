"""Exercise readiness HTTP status and DB checks without external connections."""
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

import erclave_common.health as health_module


@pytest.fixture
def readiness_client(monkeypatch):
    settings = SimpleNamespace(environment="qa", service_name="admin-service", effective_database_url="configured")
    monkeypatch.setattr(health_module, "get_settings", lambda: settings)
    app = FastAPI()
    app.include_router(health_module.router)
    return TestClient(app), settings


@pytest.mark.parametrize("environment", ["qa", "prod"])
@pytest.mark.parametrize("database_ready", [True, False])
def test_remote_ready_status_reflects_database_probe(readiness_client, monkeypatch, environment, database_ready):
    client, settings = readiness_client
    settings.environment = environment
    calls = []

    def probe(database_url):
        calls.append(database_url)
        return database_ready

    monkeypatch.setattr(health_module, "database_readiness", probe)
    result = client.get("/ready")
    assert result.status_code == (200 if database_ready else 503)
    assert result.json()["status"] == ("ready" if database_ready else "degraded")
    assert result.json()["database_ready"] is database_ready
    assert calls == ["configured"]


def test_remote_unconfigured_database_is_503_without_probe(readiness_client, monkeypatch):
    client, settings = readiness_client
    settings.effective_database_url = None
    monkeypatch.setattr(health_module, "database_readiness", lambda _: pytest.fail("Missing URL must not open a connection"))
    result = client.get("/ready")
    assert result.status_code == 503
    assert result.json()["database_configured"] is False
    assert result.json()["database_ready"] is False


@pytest.mark.parametrize("configured", [True, False])
def test_local_ready_preserves_nonprobing_behavior(readiness_client, monkeypatch, configured):
    client, settings = readiness_client
    settings.environment = "local"
    settings.effective_database_url = "configured" if configured else None
    monkeypatch.setattr(health_module, "database_readiness", lambda _: pytest.fail("Local readiness must not probe"))
    result = client.get("/ready")
    assert result.status_code == 200
    assert result.json()["database_ready"] is configured


@pytest.mark.parametrize("actual_heads,expected", [(["0062"], True), (["0036"], False), ([], False), (["0062", "other"], False)])
def test_database_probe_requires_exact_runtime_migration_heads(monkeypatch, actual_heads, expected):
    queries = []

    class Connection:
        def execute(self, statement):
            queries.append(str(statement))
            return SimpleNamespace(scalars=lambda: actual_heads)

    @contextmanager
    def connect():
        yield Connection()

    monkeypatch.setattr(health_module, "readiness_engine", lambda _: SimpleNamespace(connect=connect))
    monkeypatch.setattr(health_module, "expected_schema_heads", lambda: frozenset({"0062"}))
    assert health_module.database_readiness("configured") is expected
    assert queries == ["select version_num from alembic_version"]


@pytest.mark.parametrize("failure", [SQLAlchemyError("Synthetic unavailable database"), OSError("Synthetic connection failure")])
def test_database_probe_connection_failures_are_not_ready(monkeypatch, failure):
    def unavailable(_):
        raise failure

    monkeypatch.setattr(health_module, "readiness_engine", unavailable)
    assert health_module.database_readiness("configured") is False
