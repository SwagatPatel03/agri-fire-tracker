"""Pydantic schemas for alerts."""

from datetime import datetime
from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: int
    district_name: str
    alert_level: str
    fire_count: int
    message: str
    created_at: datetime
    acknowledged_at: datetime | None

    model_config = {"from_attributes": True}
