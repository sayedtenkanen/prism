import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ReviewJob(BaseModel):
    owner: str
    repo: str
    pr_number: int
    scm_token: str
    scm_provider: str = "github"
    hitl_enabled: bool = True
    llm_model: str = "gpt-4o"


class Daemon:
    """Prism daemon with APScheduler for periodic reviews."""

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self._jobs: dict[str, ReviewJob] = {}

    def start(self) -> None:
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("Daemon started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if getattr(self.scheduler, "running", False):
            self.scheduler.shutdown()
            logger.info("Daemon stopped")
        else:
            logger.info("Daemon stop requested but scheduler is not running")

    def add_review_job(
        self,
        job_id: str,
        job: ReviewJob,
        trigger: str = "interval",
        **trigger_kwargs: str | int,
    ) -> None:
        """Add a periodic review job."""
        if trigger == "interval":
            trig = IntervalTrigger(**trigger_kwargs)
        elif trigger == "cron":
            trig = CronTrigger(**trigger_kwargs)
        else:
            raise ValueError(f"Unknown trigger: {trigger}")

        self.scheduler.add_job(
            self._execute_review,
            trigger=trig,
            args=[job],
            id=job_id,
            replace_existing=True,
        )
        self._jobs[job_id] = job
        logger.info(f"Added job {job_id}: {job.owner}/{job.repo}#{job.pr_number}")

    def remove_review_job(self, job_id: str) -> None:
        """Remove a review job."""
        self.scheduler.remove_job(job_id)
        self._jobs.pop(job_id, None)
        logger.info(f"Removed job {job_id}")

    def list_jobs(self) -> dict[str, ReviewJob]:
        """List all scheduled jobs."""
        return self._jobs.copy()

    async def _execute_review(self, job: ReviewJob) -> None:
        """Execute a review job."""
        from app.graph.builder import get_graph
        from app.graph.state import create_initial_state

        logger.info(f"Executing review: {job.owner}/{job.repo}#{job.pr_number}")

        try:
            graph = get_graph()
            initial_state = create_initial_state(
                owner=job.owner,
                repo=job.repo,
                pr_number=job.pr_number,
                scm_token=job.scm_token,
                scm_provider=job.scm_provider,
                hitl_enabled=job.hitl_enabled,
                llm_model=job.llm_model,
            )

            result = await graph.ainvoke(initial_state)
            logger.info(f"Review completed: {result.get('approved', False)}")

        except Exception:
            logger.exception(f"Review failed for {job.owner}/{job.repo}#{job.pr_number}")


daemon = Daemon()
