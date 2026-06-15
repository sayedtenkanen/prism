"""Unit tests for Daemon and job management."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError

from app.daemon import Daemon, ReviewJob


@pytest.fixture
def daemon() -> Daemon:
    """Provide a Daemon instance."""
    return Daemon()


@pytest.fixture
def review_job() -> ReviewJob:
    """Provide a ReviewJob instance."""
    return ReviewJob(
        owner="test-owner",
        repo="test-repo",
        pr_number=42,
        scm_token="test-token",
        scm_provider="github",
        hitl_enabled=True,
        llm_model="gpt-4o",
    )


class TestReviewJob:
    """Tests for ReviewJob model."""

    def test_review_job_creation(self, review_job: ReviewJob) -> None:
        """Test ReviewJob creation with required fields."""
        assert review_job.owner == "test-owner"
        assert review_job.repo == "test-repo"
        assert review_job.pr_number == 42
        assert review_job.scm_token == "test-token"

    def test_review_job_defaults(self) -> None:
        """Test ReviewJob default values."""
        job = ReviewJob(
            owner="owner",
            repo="repo",
            pr_number=1,
            scm_token="token",
        )
        assert job.scm_provider == "github"
        assert job.hitl_enabled is True
        assert job.llm_model == "gpt-4o"


class TestDaemonStartStop:
    """Tests for Daemon start/stop behavior."""

    def test_daemon_start(self, daemon: Daemon) -> None:
        """Test daemon start initializes scheduler."""
        with patch.object(daemon.scheduler, "start") as mock_start:
            daemon.start()
            mock_start.assert_called_once()

    def test_daemon_stop_when_running(self, daemon: Daemon) -> None:
        """Test daemon stop when scheduler is running."""
        daemon.scheduler.running = True
        with patch.object(daemon.scheduler, "shutdown") as mock_shutdown:
            daemon.stop()
            mock_shutdown.assert_called_once()

    def test_daemon_stop_when_not_running(self, daemon: Daemon) -> None:
        """Test daemon stop when scheduler is not running."""
        daemon.scheduler.running = False
        with patch.object(daemon.scheduler, "shutdown") as mock_shutdown:
            daemon.stop()
            mock_shutdown.assert_not_called()


class TestDaemonJobManagement:
    """Tests for Daemon job management."""

    def test_add_review_job_interval(self, daemon: Daemon, review_job: ReviewJob) -> None:
        """Test adding a job with interval trigger."""
        with patch.object(daemon.scheduler, "add_job") as mock_add:
            daemon.add_review_job(
                "job-1",
                review_job,
                trigger="interval",
                seconds=3600,
            )
            mock_add.assert_called_once()
            assert "job-1" in daemon._jobs

    def test_add_review_job_cron(self, daemon: Daemon, review_job: ReviewJob) -> None:
        """Test adding a job with cron trigger."""
        with patch.object(daemon.scheduler, "add_job") as mock_add:
            daemon.add_review_job(
                "job-2",
                review_job,
                trigger="cron",
                hour="12",
                minute="0",
                day="*",
                month="*",
                day_of_week="*",
            )
            mock_add.assert_called_once()
            assert "job-2" in daemon._jobs

    def test_add_review_job_invalid_trigger(self, daemon: Daemon, review_job: ReviewJob) -> None:
        """Test adding a job with invalid trigger raises error."""
        with pytest.raises(ValueError, match="Unknown trigger"):
            daemon.add_review_job(
                "job-invalid",
                review_job,
                trigger="invalid",
            )

    def test_remove_review_job(self, daemon: Daemon, review_job: ReviewJob) -> None:
        """Test removing a review job."""
        with patch.object(daemon.scheduler, "add_job"):
            daemon.add_review_job("job-1", review_job, trigger="interval", seconds=3600)

        with patch.object(daemon.scheduler, "remove_job") as mock_remove:
            daemon.remove_review_job("job-1")
            mock_remove.assert_called_once_with("job-1")
            assert "job-1" not in daemon._jobs

    def test_remove_nonexistent_job(self, daemon: Daemon) -> None:
        """Test removing a nonexistent job doesn't error."""
        # Should not raise
        daemon.remove_review_job("nonexistent")

    def test_list_jobs(self, daemon: Daemon, review_job: ReviewJob) -> None:
        """Test listing all jobs."""
        with patch.object(daemon.scheduler, "add_job"):
            daemon.add_review_job("job-1", review_job, trigger="interval", seconds=3600)
            daemon.add_review_job("job-2", review_job, trigger="interval", seconds=7200)

        jobs = daemon.list_jobs()
        assert len(jobs) == 2
        assert "job-1" in jobs
        assert "job-2" in jobs

    def test_list_jobs_returns_copy(self, daemon: Daemon, review_job: ReviewJob) -> None:
        """Test list_jobs returns a copy to prevent external mutations."""
        with patch.object(daemon.scheduler, "add_job"):
            daemon.add_review_job("job-1", review_job, trigger="interval", seconds=3600)

        jobs_list = daemon.list_jobs()
        jobs_list.clear()  # Mutate the returned copy
        assert len(daemon.list_jobs()) == 1  # Original unchanged


class TestDaemonExecuteReview:
    """Tests for Daemon review execution."""

    @pytest.mark.asyncio
    async def test_execute_review_success(self, daemon: Daemon, review_job: ReviewJob) -> None:
        """Test successful review execution."""
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {
            "summary": "Test summary",
            "approved": True,
        }

        with patch("app.daemon.get_graph", return_value=mock_graph):
            with patch("app.daemon.create_initial_state", return_value={}):
                await daemon._execute_review(review_job)
                mock_graph.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_review_error_handling(self, daemon: Daemon, review_job: ReviewJob) -> None:
        """Test review execution with error."""
        mock_graph = AsyncMock()
        mock_graph.ainvoke.side_effect = Exception("Graph execution failed")

        with patch("app.daemon.get_graph", return_value=mock_graph):
            with patch("app.daemon.create_initial_state", return_value={}):
                # Should not raise; error is logged
                await daemon._execute_review(review_job)
                mock_graph.ainvoke.assert_called_once()
