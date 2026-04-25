from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Enum
import enum

from app.db.database import Base


class AlertLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Alert(Base):
    """Threshold-based fire alert for a district."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    district_name = Column(String, index=True, nullable=False)
    alert_level = Column(Enum(AlertLevel), nullable=False)
    fire_count = Column(Integer, nullable=False)
    message = Column(String, nullable=False)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    acknowledged_at = Column(DateTime, nullable=True)
