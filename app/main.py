import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from apscheduler.jobstores.base import JobLookupError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.daemon import ReviewJob, daemon

logger = logging.getLogger(__name__)

HEALTH_RESPONSE: dict[str, str] = {"status": "healthy"}


class ReviewRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int
    scm_token: str
    scm_provider: str = "github"
    hitl_enabled: bool = True
    llm_model: str = "gpt-4o"


class ReviewResponse(BaseModel):
    summary: str | None = None
    approved: bool = False
    critical_findings: list[dict] = []
    major_findings: list[dict] = []
    minor_findings: list[dict] = []


class JobRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int
    scm_token: str
    scm_provider: str = "github"
    hitl_enabled: bool = True
    llm_model: str = "gpt-4o"
    trigger: str = "interval"
    interval_seconds: int | None = None
    cron_expression: str | None = None


class JobResponse(BaseModel):
    job_id: str
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    daemon.start()
    yield
    daemon.stop()


app = FastAPI(
    title="Prism",
    description="Pull Request Inspection, Synthesis & Monitoring",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/health/")
async def health_check() -> dict[str, str]:
    return HEALTH_RESPONSE


@app.get("/api/v1/health/")
async def api_health_check() -> dict[str, str]:
    return HEALTH_RESPONSE


@app.post("/api/v1/review/", response_model=ReviewResponse)
async def review_pr(request: ReviewRequest) -> ReviewResponse:
    from app.graph.builder import get_graph
    from app.graph.state import create_initial_state

    graph = get_graph()
    initial_state = create_initial_state(
        owner=request.owner,
        repo=request.repo,
        pr_number=request.pr_number,
        scm_token=request.scm_token,
        scm_provider=request.scm_provider,
        hitl_enabled=request.hitl_enabled,
        llm_model=request.llm_model,
    )

    try:
        result = await graph.ainvoke(initial_state)
    except Exception as e:
        logger.exception("Review execution failed")
        raise HTTPException(status_code=500, detail="Review execution failed") from e

    return ReviewResponse(
        summary=result.get("summary"),
        approved=result.get("approved", False),
        critical_findings=result.get("critical_findings", []),
        major_findings=result.get("major_findings", []),
        minor_findings=result.get("minor_findings", []),
    )


@app.post("/api/v1/jobs/", response_model=JobResponse)
async def create_job(request: JobRequest) -> JobResponse:
    job = ReviewJob(
        owner=request.owner,
        repo=request.repo,
        pr_number=request.pr_number,
        scm_token=request.scm_token,
        scm_provider=request.scm_provider,
        hitl_enabled=request.hitl_enabled,
        llm_model=request.llm_model,
    )

    job_id = f"{request.owner}/{request.repo}#{request.pr_number}"

    if request.trigger not in {"interval", "cron"}:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid trigger '{request.trigger}'. Supported values are 'interval' and 'cron'.",
        )

    trigger_kwargs: dict[str, str | int] = {}

    if request.trigger == "interval":
        if request.interval_seconds is None or request.interval_seconds <= 0:
            raise HTTPException(
                status_code=400,
                detail="For 'interval' trigger, 'interval_seconds' must be a positive integer.",
            )
        trigger_kwargs["seconds"] = request.interval_seconds

    elif request.trigger == "cron":
        if not request.cron_expression:
            raise HTTPException(
                status_code=400,
                detail="For 'cron' trigger, 'cron_expression' is required.",
            )

        parts = [p for p in request.cron_expression.split() if p]
        if len(parts) != 5:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid 'cron_expression'. Expected 5 fields separated by spaces: "
                    "'minute hour day month day_of_week'."
                ),
            )

        trigger_kwargs = {
            "minute": parts[0],
            "hour": parts[1],
            "day": parts[2],
            "month": parts[3],
            "day_of_week": parts[4],
        }

    daemon.add_review_job(job_id, job, trigger=request.trigger, **trigger_kwargs)

    return JobResponse(job_id=job_id, status="created")


@app.delete("/api/v1/jobs/{job_id}")
async def delete_job(job_id: str) -> dict[str, str]:
    try:
        daemon.remove_review_job(job_id)
    except JobLookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return {"status": "deleted"}


@app.get("/api/v1/jobs/")
async def list_jobs() -> dict[str, str]:
    jobs = daemon.list_jobs()
    return {job_id: f"{job.owner}/{job.repo}#{job.pr_number}" for job_id, job in jobs.items()}
