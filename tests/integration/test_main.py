"""Integration tests for FastAPI endpoints."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from apscheduler.jobstores.base import JobLookupError

from app.main import (
    app,
    ReviewRequest,
    ReviewResponse,
    JobRequest,
    JobResponse,
)


@pytest.fixture
def client() -> TestClient:
    """Provide a FastAPI test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check_root(self, client: TestClient) -> None:
        """Test root health endpoint."""
        response = client.get("/health/")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_health_check_api(self, client: TestClient) -> None:
        """Test API health endpoint."""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestReviewEndpoint:
    """Tests for review endpoint."""

    @patch("app.main.get_graph")
    def test_review_success(self, mock_get_graph, client: TestClient) -> None:
        """Test successful review request."""
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {
            "summary": "All checks passed",
            "approved": True,
            "critical_findings": [],
            "major_findings": [],
            "minor_findings": [],
        }
        mock_get_graph.return_value = mock_graph

        review_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 42,
            "scm_token": "test-token",
        }

        response = client.post("/api/v1/review/", json=review_data)
        assert response.status_code == 200
        result = response.json()
        assert result["summary"] == "All checks passed"
        assert result["approved"] is True

    @patch("app.main.get_graph")
    def test_review_with_findings(self, mock_get_graph, client: TestClient) -> None:
        """Test review request with findings."""
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {
            "summary": "Issues found",
            "approved": False,
            "critical_findings": [{"finding": "SQL injection risk"}],
            "major_findings": [{"finding": "Performance issue"}],
            "minor_findings": [{"finding": "Style issue"}],
        }
        mock_get_graph.return_value = mock_graph

        review_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 42,
            "scm_token": "test-token",
        }

        response = client.post("/api/v1/review/", json=review_data)
        assert response.status_code == 200
        result = response.json()
        assert result["approved"] is False
        assert len(result["critical_findings"]) == 1
        assert len(result["major_findings"]) == 1
        assert len(result["minor_findings"]) == 1

    @patch("app.main.get_graph")
    def test_review_execution_error(self, mock_get_graph, client: TestClient) -> None:
        """Test review request with execution error."""
        mock_graph = AsyncMock()
        mock_graph.ainvoke.side_effect = Exception("Graph execution failed")
        mock_get_graph.return_value = mock_graph

        review_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 42,
            "scm_token": "test-token",
        }

        response = client.post("/api/v1/review/", json=review_data)
        assert response.status_code == 500
        assert "Review execution failed" in response.json()["detail"]

    def test_review_custom_model(self, client: TestClient) -> None:
        """Test review with custom LLM model."""
        with patch("app.main.get_graph") as mock_get_graph:
            mock_graph = AsyncMock()
            mock_graph.ainvoke.return_value = {
                "summary": "Test",
                "approved": True,
                "critical_findings": [],
                "major_findings": [],
                "minor_findings": [],
            }
            mock_get_graph.return_value = mock_graph

            review_data = {
                "owner": "test-owner",
                "repo": "test-repo",
                "pr_number": 42,
                "scm_token": "test-token",
                "llm_model": "gpt-4",
            }

            response = client.post("/api/v1/review/", json=review_data)
            assert response.status_code == 200


class TestJobEndpoints:
    """Tests for job management endpoints."""

    def test_create_job_interval(self, client: TestClient) -> None:
        """Test creating a job with interval trigger."""
        job_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 42,
            "scm_token": "test-token",
            "trigger": "interval",
            "interval_seconds": 3600,
        }

        with patch("app.main.daemon.add_review_job"):
            response = client.post("/api/v1/jobs/", json=job_data)
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "created"
            assert "job_id" in result

    def test_create_job_cron(self, client: TestClient) -> None:
        """Test creating a job with cron trigger."""
        job_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 42,
            "scm_token": "test-token",
            "trigger": "cron",
            "cron_expression": "0 12 * * *",  # Daily at noon
        }

        with patch("app.main.daemon.add_review_job"):
            response = client.post("/api/v1/jobs/", json=job_data)
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "created"

    def test_create_job_invalid_trigger(self, client: TestClient) -> None:
        """Test creating a job with invalid trigger."""
        job_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 42,
            "scm_token": "test-token",
            "trigger": "invalid",
        }

        response = client.post("/api/v1/jobs/", json=job_data)
        assert response.status_code == 400
        assert "Invalid trigger" in response.json()["detail"]

    def test_create_job_interval_missing_seconds(self, client: TestClient) -> None:
        """Test creating interval job without interval_seconds."""
        job_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 42,
            "scm_token": "test-token",
            "trigger": "interval",
        }

        response = client.post("/api/v1/jobs/", json=job_data)
        assert response.status_code == 400
        assert "interval_seconds" in response.json()["detail"]

    def test_create_job_interval_negative_seconds(self, client: TestClient) -> None:
        """Test creating interval job with negative interval_seconds."""
        job_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 42,
            "scm_token": "test-token",
            "trigger": "interval",
            "interval_seconds": -1,
        }

        response = client.post("/api/v1/jobs/", json=job_data)
        assert response.status_code == 400
        assert "positive integer" in response.json()["detail"]

    def test_create_job_cron_missing_expression(self, client: TestClient) -> None:
        """Test creating cron job without cron_expression."""
        job_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 42,
            "scm_token": "test-token",
            "trigger": "cron",
        }

        response = client.post("/api/v1/jobs/", json=job_data)
        assert response.status_code == 400
        assert "cron_expression" in response.json()["detail"]

    def test_create_job_cron_invalid_expression(self, client: TestClient) -> None:
        """Test creating cron job with invalid cron_expression."""
        job_data = {
            "owner": "test-owner",
            "repo": "test-repo",
            "pr_number": 42,
            "scm_token": "test-token",
            "trigger": "cron",
            "cron_expression": "invalid cron",  # Too few fields
        }

        response = client.post("/api/v1/jobs/", json=job_data)
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]

    def test_delete_job_success(self, client: TestClient) -> None:
        """Test deleting a job successfully."""
        with patch("app.main.daemon.remove_review_job"):
            response = client.delete("/api/v1/jobs/test-owner%2Ftest-repo%231")
            assert response.status_code == 200
            assert response.json() == {"status": "deleted"}

    def test_delete_job_not_found(self, client: TestClient) -> None:
        """Test deleting a nonexistent job."""
        with patch("app.main.daemon.remove_review_job") as mock_remove:
            mock_remove.side_effect = JobLookupError("Job not found")
            response = client.delete("/api/v1/jobs/nonexistent")
            assert response.status_code == 404
            assert "Job not found" in response.json()["detail"]

    def test_list_jobs_empty(self, client: TestClient) -> None:
        """Test listing jobs when none exist."""
        with patch("app.main.daemon.list_jobs", return_value={}):
            response = client.get("/api/v1/jobs/")
            assert response.status_code == 200
            assert response.json() == {}

    def test_list_jobs_with_jobs(self, client: TestClient) -> None:
        """Test listing jobs when multiple jobs exist."""
        mock_jobs = {
            "job-1": MagicMock(owner="owner1", repo="repo1", pr_number=1),
            "job-2": MagicMock(owner="owner2", repo="repo2", pr_number=2),
        }
        with patch("app.main.daemon.list_jobs", return_value=mock_jobs):
            response = client.get("/api/v1/jobs/")
            assert response.status_code == 200
            jobs = response.json()
            assert len(jobs) == 2
            assert "job-1" in jobs
            assert "job-2" in jobs
