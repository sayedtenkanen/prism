from fastapi import FastAPI

app = FastAPI(
    title="Prism",
    description="Pull Request Inspection, Synthesis & Monitoring",
    version="0.1.0",
)

HEALTH_RESPONSE: dict[str, str] = {"status": "healthy"}


@app.get("/health/")
async def health_check() -> dict[str, str]:
    return HEALTH_RESPONSE


@app.get("/api/v1/health/")
async def api_health_check() -> dict[str, str]:
    return HEALTH_RESPONSE
