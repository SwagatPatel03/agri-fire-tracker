from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, UniqueConstraint
)
from geoalchemy2 import Geometry

from app.db.database import Base


class Fire(Base):
    """An active fire detection from NASA FIRMS satellite data."""

    __tablename__ = "active_fires"
    __table_args__ = (
        # Proper idempotency — same location + time = same fire
        UniqueConstraint("latitude", "longitude", "detected_at", name="uq_fire_location_time"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Raw coordinates (for easy querying without PostGIS decode)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # PostGIS Point geometry (SRID 4326 = GPS WGS84)
    location = Column(Geometry(geometry_type="POINT", srid=4326))

    # Predicted smoke plume polygon (Gaussian dispersion model)
    trajectory = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)

    # Fire characteristics
    magnitude = Column(Float)               # FRP — Fire Radiative Power (MW)
    confidence = Column(String, nullable=True)  # NASA confidence level (low/nominal/high)
    satellite = Column(String, nullable=True)   # Source sensor (e.g., "VIIRS_SNPP_NRT")

    # Weather data at time of detection
    wind_speed = Column(Float)               # km/h
    wind_direction = Column(Float)           # Degrees (0-360, meteorological)

    # Temporal data
    detected_at = Column(DateTime, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Administrative
    district_name = Column(String, index=True, default="Unknown")

    # Retention management
    is_active = Column(Boolean, default=True, index=True)