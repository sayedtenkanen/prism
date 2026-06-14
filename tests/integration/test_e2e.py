import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


async def test_api_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


async def test_list_jobs_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/jobs/")
    assert response.status_code == 200
    assert response.json() == {}


async def test_create_job_invalid_trigger(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/jobs/",
        json={
            "owner": "test",
            "repo": "repo",
            "pr_number": 1,
            "scm_token": "token",
            "trigger": "invalid",
        },
    )
    assert response.status_code == 400
    assert "Invalid trigger" in response.json()["detail"]


async def test_create_job_interval_missing_seconds(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/jobs/",
        json={
            "owner": "test",
            "repo": "repo",
            "pr_number": 1,
            "scm_token": "token",
            "trigger": "interval",
        },
    )
    assert response.status_code == 400
    assert "interval_seconds" in response.json()["detail"]


async def test_create_job_cron_missing_expression(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/jobs/",
        json={
            "owner": "test",
            "repo": "repo",
            "pr_number": 1,
            "scm_token": "token",
            "trigger": "cron",
        },
    )
    assert response.status_code == 400
    assert "cron_expression" in response.json()["detail"]


async def test_create_job_cron_invalid_format(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/jobs/",
        json={
            "owner": "test",
            "repo": "repo",
            "pr_number": 1,
            "scm_token": "token",
            "trigger": "cron",
            "cron_expression": "* *",
        },
    )
    assert response.status_code == 400
    assert "5 fields" in response.json()["detail"]


async def test_delete_job_not_found(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/jobs/nonexistent")
    assert response.status_code == 404
