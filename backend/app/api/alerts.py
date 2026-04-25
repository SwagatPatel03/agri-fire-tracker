"""Alert API endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertResponse

router = APIRouter()


@router.get("/alerts", response_model=list[AlertResponse])
def get_alerts(
    limit: int = 50,
    unacknowledged_only: bool = True,
    db: Session = Depends(get_db),
):
    """List recent alerts, optionally filtered to unacknowledged only."""
    query = db.query(Alert)

    if unacknowledged_only:
        query = query.filter(Alert.acknowledged_at.is_(None))

    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    return alerts


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Mark an alert as acknowledged."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return {"error": "Alert not found"}

    alert.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "acknowledged", "alert_id": alert_id}
