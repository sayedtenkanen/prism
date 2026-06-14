import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_api_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_list_jobs_empty(client: TestClient) -> None:
    response = client.get("/api/v1/jobs/")
    assert response.status_code == 200
    assert response.json() == {}
