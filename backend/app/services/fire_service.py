"""
Fire ingestion service — fetches NASA FIRMS data, enriches with weather,
calculates Gaussian smoke plumes, resolves districts, and saves to PostGIS.
"""

import csv
from datetime import datetime
from io import StringIO

import httpx
from shapely.geometry import Point
from sqlalchemy import func

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.models.fire import Fire
from app.models.district import District
from app.models.alert import Alert, AlertLevel
from app.services.weather_service import get_wind_data
from app.services.plume_service import calculate_gaussian_plume

logger = get_logger(__name__)

# NASA FIRMS bounding box for India (west, south, east, north)
INDIA_BBOX = "68,6,98,38"
NASA_SENSOR = "VIIRS_SNPP_NRT"
NASA_DAY_RANGE = 2  # Fetch last 2 days of data

# Alert thresholds (fires per district to trigger alert level)
ALERT_THRESHOLDS = {
    AlertLevel.LOW: 3,
    AlertLevel.MEDIUM: 10,
    AlertLevel.HIGH: 25,
    AlertLevel.CRITICAL: 50,
}


def _resolve_district(db, lat: float, lon: float) -> str:
    """Find which district contains this coordinate using PostGIS ST_Contains."""
    point_wkt = f"SRID=4326;POINT({lon} {lat})"
    result = db.query(District.name).filter(
        func.ST_Contains(District.boundary, func.ST_GeomFromEWKT(point_wkt))
    ).first()
    return result[0] if result else "Unknown"


def _check_and_create_alerts(db, fire_counts: dict[str, int]) -> None:
    """Create alerts for districts exceeding fire count thresholds."""
    for district_name, count in fire_counts.items():
        if district_name == "Unknown":
            continue

        # Find the highest applicable alert level
        alert_level = None
        for level, threshold in sorted(
            ALERT_THRESHOLDS.items(), key=lambda x: x[1], reverse=True
        ):
            if count >= threshold:
                alert_level = level
                break

        if alert_level is None:
            continue

        # Check if we already have an unacknowledged alert at this level for this district
        existing = db.query(Alert).filter(
            Alert.district_name == district_name,
            Alert.alert_level == alert_level,
            Alert.acknowledged_at.is_(None),
        ).first()

        if not existing:
            alert = Alert(
                district_name=district_name,
                alert_level=alert_level,
                fire_count=count,
                message=f"{count} active fires detected in {district_name}",
            )
            db.add(alert)
            logger.warning(f"ALERT created: {alert_level.value} for {district_name} ({count} fires)")


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def fetch_and_process_nasa_fires(self):
    """
    Background job: Fetch NASA fire data → enrich with weather →
    compute smoke plumes → resolve districts → save to PostGIS.
    """
    db = SessionLocal()
    weather_cache: dict[str, tuple[float, float]] = {}
    fire_counts: dict[str, int] = {}  # District → fire count for alerting
    stats = {"fetched": 0, "new": 0, "skipped": 0, "errors": 0}

    try:
        # ── 1. FETCH from NASA FIRMS ──────────────────────────
        nasa_url = (
            f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
            f"{settings.NASA_FIRMS_API_KEY}/{NASA_SENSOR}/{INDIA_BBOX}/{NASA_DAY_RANGE}"
        )
        logger.info(f"Fetching fire data from NASA FIRMS ({NASA_SENSOR}, {NASA_DAY_RANGE} days)")

        with httpx.Client(timeout=30.0) as client:
            nasa_response = client.get(nasa_url)

        if nasa_response.status_code != 200:
            logger.error(f"NASA API error: {nasa_response.status_code} — {nasa_response.text[:200]}")
            raise self.retry(exc=Exception(f"NASA API returned {nasa_response.status_code}"))

        # ── 2. PARSE CSV ──────────────────────────────────────
        csv_stream = StringIO(nasa_response.text)
        csv_reader = csv.DictReader(csv_stream)

        for row in csv_reader:
            stats["fetched"] += 1

            try:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                frp = float(row["frp"])
                confidence = row.get("confidence", "nominal")

                # Parse acquisition datetime
                acq_date = row["acq_date"]
                acq_time = row["acq_time"].zfill(4)
                fire_time = datetime.strptime(f"{acq_date} {acq_time}", "%Y-%m-%d %H%M")

                # ── 3. IDEMPOTENCY CHECK (lat + lon + time) ───
                existing = db.query(Fire.id).filter(
                    Fire.latitude == lat,
                    Fire.longitude == lon,
                    Fire.detected_at == fire_time,
                ).first()

                if existing:
                    stats["skipped"] += 1
                    continue

                # ── 4. WEATHER ENRICHMENT (Open-Meteo) ────────
                wind_speed, wind_deg = get_wind_data(lat, lon, cache=weather_cache)

                # ── 5. GAUSSIAN PLUME CALCULATION ─────────────
                plume_polygon = calculate_gaussian_plume(
                    lat, lon, wind_speed, wind_deg,
                    duration_hours=6.0,
                    stability_class="D",
                )
                fire_point = Point(lon, lat)

                # ── 6. DISTRICT RESOLUTION ────────────────────
                district_name = _resolve_district(db, lat, lon)

                # Track fire counts per district for alerting
                fire_counts[district_name] = fire_counts.get(district_name, 0) + 1

                # ── 7. SAVE TO DATABASE ───────────────────────
                new_fire = Fire(
                    latitude=lat,
                    longitude=lon,
                    location=f"SRID=4326;{fire_point.wkt}",
                    trajectory=f"SRID=4326;{plume_polygon.wkt}",
                    magnitude=frp,
                    confidence=confidence,
                    satellite=NASA_SENSOR,
                    wind_speed=wind_speed,
                    wind_direction=wind_deg,
                    detected_at=fire_time,
                    district_name=district_name,
                )
                db.add(new_fire)
                stats["new"] += 1

            except (KeyError, ValueError) as e:
                stats["errors"] += 1
                logger.warning(f"Skipping malformed fire row: {e}")
                continue

        # Commit all new fires at once
        db.commit()

        # ── 8. GENERATE ALERTS ────────────────────────────────
        _check_and_create_alerts(db, fire_counts)
        db.commit()

        logger.info(
            f"Fire ingestion complete: "
            f"fetched={stats['fetched']}, new={stats['new']}, "
            f"skipped={stats['skipped']}, errors={stats['errors']}"
        )

    except Exception as e:
        logger.error(f"Fire processing failed: {e}")
        db.rollback()
        raise self.retry(exc=e)

    finally:
        db.close()