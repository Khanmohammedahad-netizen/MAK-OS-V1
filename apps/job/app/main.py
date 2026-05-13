"""MAK Lead Engine — FastAPI application.

Single POST /run-daily endpoint invoked by Cloud Scheduler.
Health check at GET /health.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Response

from app.config import Settings, get_settings
from app.pipeline import run_daily_pipeline
from app.utils.logging import setup_logging

app = FastAPI(
    title="MAK Lead Engine",
    description="Autonomous B2B lead generation pipeline",
    version="1.0.0",
)


@app.on_event("startup")
def startup() -> None:
    """Configure logging on startup."""
    settings = get_settings()
    setup_logging(log_level=settings.log_level, log_format=settings.log_format)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint for Cloud Run."""
    return {"status": "ok", "service": "mak-lead-engine"}


@app.post("/run-daily")
def run_daily() -> dict[str, Any]:
    """Execute the daily lead generation pipeline.

    Called by Cloud Scheduler or manually from the dashboard.
    """
    try:
        settings = get_settings()
        result = run_daily_pipeline(settings)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
