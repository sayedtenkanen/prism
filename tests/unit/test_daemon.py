import pytest
from apscheduler.jobstores.base import JobLookupError

from app.daemon import Daemon, ReviewJob


def test_daemon_init() -> None:
    daemon = Daemon()
    assert daemon._jobs == {}


def test_daemon_add_job() -> None:
    daemon = Daemon()
    job = ReviewJob(
        owner="test",
        repo="repo",
        pr_number=1,
        scm_token="token",
    )
    daemon.add_review_job(
        "test/repo#1",
        job,
        trigger="interval",
        seconds=60,
    )
    assert "test/repo#1" in daemon._jobs


def test_daemon_list_jobs() -> None:
    daemon = Daemon()
    job = ReviewJob(
        owner="test",
        repo="repo",
        pr_number=1,
        scm_token="token",
    )
    daemon.add_review_job(
        "test/repo#1",
        job,
        trigger="interval",
        seconds=60,
    )
    jobs = daemon.list_jobs()
    assert len(jobs) == 1
    assert "test/repo#1" in jobs


def test_daemon_remove_job() -> None:
    daemon = Daemon()
    job = ReviewJob(
        owner="test",
        repo="repo",
        pr_number=1,
        scm_token="token",
    )
    daemon.add_review_job(
        "test/repo#1",
        job,
        trigger="interval",
        seconds=60,
    )
    daemon.remove_review_job("test/repo#1")
    assert "test/repo#1" not in daemon._jobs


def test_daemon_remove_nonexistent_job() -> None:
    daemon = Daemon()
    with pytest.raises(JobLookupError):
        daemon.remove_review_job("nonexistent")


def test_review_job_model() -> None:
    job = ReviewJob(
        owner="test",
        repo="repo",
        pr_number=1,
        scm_token="token",
    )
    assert job.owner == "test"
    assert job.repo == "repo"
    assert job.pr_number == 1
    assert job.scm_provider == "github"
    assert job.hitl_enabled is True
    assert job.llm_model == "gpt-4o"
