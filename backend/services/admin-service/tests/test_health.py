from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_correlation_id_is_returned():
    client = TestClient(app)
    response = client.get("/health", headers={"X-Correlation-Id": "corr_test"})

    assert response.headers["X-Correlation-Id"] == "corr_test"

