"""
Seed the districts table with India's district boundaries.

Downloads district GeoJSON from datta07/INDIAN-SHAPEFILES on GitHub
and loads it into PostGIS.

Usage:
    python -m app.scripts.seed_districts
"""

import sys
import json
from pathlib import Path

import httpx
from shapely.geometry import shape, MultiPolygon, Polygon

from app.db.database import SessionLocal
from app.models.district import District
from app.core.logging import setup_logging, get_logger

logger = get_logger(__name__)

# datta07/INDIAN-SHAPEFILES district boundaries (GeoJSON, ~78 MB)
GEOJSON_URL = (
    "https://raw.githubusercontent.com/datta07/INDIAN-SHAPEFILES/master/"
    "INDIA/INDIA_DISTRICTS.geojson"
)

LOCAL_CACHE = Path(__file__).parent.parent.parent / "data" / "districts" / "india_districts.geojson"


def download_geojson() -> dict:
    """Download or load cached district GeoJSON."""
    if LOCAL_CACHE.exists():
        logger.info(f"Loading cached GeoJSON from {LOCAL_CACHE}")
        return json.loads(LOCAL_CACHE.read_text(encoding="utf-8"))

    logger.info(f"Downloading district boundaries from {GEOJSON_URL}")
    logger.info("This is a ~78 MB file, it may take a few minutes...")

    response = httpx.get(GEOJSON_URL, timeout=300.0, follow_redirects=True)
    response.raise_for_status()

    # Cache locally
    LOCAL_CACHE.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_CACHE.write_bytes(response.content)
    logger.info(f"Cached GeoJSON to {LOCAL_CACHE}")

    return response.json()


def _process_feature(db, i: int, feature: dict) -> str:
    """
    Process a single GeoJSON feature into the districts table.
    Returns 'created', 'updated', or 'skipped'.
    """
    props = feature.get("properties", {})

    # This GeoJSON uses lowercase property names
    name = (
        props.get("district")
        or props.get("DISTRICT")
        or props.get("dtname")
        or props.get("NAME")
        or ""
    ).strip().title()

    state = (
        props.get("state")
        or props.get("STATE")
        or props.get("ST_NM")
        or props.get("stname")
        or ""
    ).strip().title()

    # Skip features without a proper district name
    if not name or name == "Unknown":
        return "skipped"

    # Parse geometry
    geom = shape(feature["geometry"])

    # Ensure it's a MultiPolygon
    if isinstance(geom, Polygon):
        geom = MultiPolygon([geom])

    # Fix invalid geometries
    if not geom.is_valid:
        geom = geom.buffer(0)
        # buffer(0) can collapse MultiPolygon -> Polygon
        if isinstance(geom, Polygon):
            geom = MultiPolygon([geom])

    # shape_area is in square meters -> convert to sq km
    area_raw = props.get("shape_area") or props.get("Shape_Area")
    area_sq_km = None
    if area_raw:
        try:
            area_sq_km = float(area_raw) / 1e6
        except (ValueError, TypeError):
            pass

    # Use state-qualified name to avoid unique constraint violations
    display_name = f"{name} ({state})" if state else name

    wkt = f"SRID=4326;{geom.wkt}"

    # Upsert: update if exists, create if not
    existing = db.query(District).filter(District.name == display_name).first()

    if existing:
        existing.state = state
        existing.boundary = wkt
        if area_sq_km:
            existing.area_sq_km = round(area_sq_km, 2)
        return "updated"
    else:
        district = District(
            name=display_name,
            state=state,
            boundary=wkt,
            area_sq_km=round(area_sq_km, 2) if area_sq_km else None,
        )
        db.add(district)
        return "created"


def seed_districts():
    """Parse GeoJSON and upsert districts into the database."""
    setup_logging()

    geojson = download_geojson()
    features = geojson.get("features", [])
    logger.info(f"Found {len(features)} district features")

    db = SessionLocal()
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

    for i, feature in enumerate(features):
        try:
            result = _process_feature(db, i, feature)
            stats[result] += 1

            # Commit in batches to avoid huge transactions
            if (stats["created"] + stats["updated"]) % 50 == 0 and (stats["created"] + stats["updated"]) > 0:
                db.commit()
                logger.info(f"Progress: {stats['created'] + stats['updated']}/{len(features)}")

        except Exception as e:
            stats["errors"] += 1
            db.rollback()  # Reset the session state after error
            logger.warning(f"Error processing feature {i}: {str(e)[:120]}")

    # Final commit
    try:
        db.commit()
    except Exception as e:
        logger.error(f"Final commit failed: {e}")
        db.rollback()

    db.close()

    logger.info(
        f"District seeding complete: "
        f"created={stats['created']}, updated={stats['updated']}, "
        f"skipped={stats['skipped']}, errors={stats['errors']}"
    )


if __name__ == "__main__":
    seed_districts()
