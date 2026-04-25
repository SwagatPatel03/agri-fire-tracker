"""System endpoints — health checks and admin operations."""

from fastapi import APIRouter, Header, HTTPException

from app.core.config import settings
from app.services.fire_service import fetch_and_process_nasa_fires

router = APIRouter()


@router.get("/system/health")
def health_check():
    """Basic health check."""
    return {"status": "healthy", "version": "2.0.0"}


@router.post("/system/trigger-fetch")
def trigger_nasa_fetch(
    x_api_key: str = Header(..., description="Admin API key"),
):
    """
    Manually trigger a NASA fire data fetch.
    Protected by API key to prevent abuse.
    """
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

    fetch_and_process_nasa_fires.delay()
    return {"message": "NASA fetch task sent to background worker"}
