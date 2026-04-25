"""Fire data API endpoints — serves GeoJSON for the map frontend."""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape

from app.db.database import get_db
from app.models.fire import Fire

router = APIRouter()


def _fire_to_geojson_feature(fire: Fire) -> dict:
    """Convert a Fire ORM object to a GeoJSON Feature."""
    point = to_shape(fire.location)
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [point.x, point.y],
        },
        "properties": {
            "id": fire.id,
            "magnitude": fire.magnitude,
            "confidence": fire.confidence,
            "satellite": fire.satellite,
            "wind_speed": fire.wind_speed,
            "wind_direction": fire.wind_direction,
            "detected_at": fire.detected_at.isoformat() if fire.detected_at else None,
            "district_name": fire.district_name,
            "is_active": fire.is_active,
        },
    }


def _plume_to_geojson_feature(fire: Fire) -> dict | None:
    """Convert a Fire's trajectory to a GeoJSON Feature."""
    if fire.trajectory is None:
        return None
    polygon = to_shape(fire.trajectory)
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [list(polygon.exterior.coords)],
        },
        "properties": {
            "fire_id": fire.id,
            "magnitude": fire.magnitude,
            "wind_speed": fire.wind_speed,
            "wind_direction": fire.wind_direction,
            "district_name": fire.district_name,
        },
    }


@router.get("/fires")
def get_fires(
    hours: int = Query(24, ge=1, le=240, description="Fires from the last N hours"),
    min_frp: float = Query(0, ge=0, description="Minimum fire radiative power"),
    district: str | None = Query(None, description="Filter by district name"),
    active_only: bool = Query(True, description="Only return active fires"),
    db: Session = Depends(get_db),
):
    """Return active fires as a GeoJSON FeatureCollection."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = db.query(Fire).filter(Fire.detected_at >= cutoff)

    if active_only:
        query = query.filter(Fire.is_active == True)  # noqa: E712

    if min_frp > 0:
        query = query.filter(Fire.magnitude >= min_frp)

    if district:
        query = query.filter(Fire.district_name == district)

    fires = query.order_by(Fire.detected_at.desc()).limit(5000).all()

    features = [_fire_to_geojson_feature(f) for f in fires]

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "count": len(features),
            "hours": hours,
            "min_frp": min_frp,
        },
    }


@router.get("/fires/plumes")
def get_plumes(
    hours: int = Query(24, ge=1, le=240),
    db: Session = Depends(get_db),
):
    """Return smoke plume trajectories as a GeoJSON FeatureCollection."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    fires = db.query(Fire).filter(
        Fire.detected_at >= cutoff,
        Fire.is_active == True,  # noqa: E712
        Fire.trajectory.isnot(None),
    ).all()

    features = [f for f in (_plume_to_geojson_feature(fire) for fire in fires) if f]

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {"count": len(features)},
    }


@router.get("/fires/{fire_id}")
def get_fire_detail(fire_id: int, db: Session = Depends(get_db)):
    """Get detailed info for a single fire including its plume."""
    fire = db.query(Fire).filter(Fire.id == fire_id).first()
    if not fire:
        return {"error": "Fire not found"}

    result = _fire_to_geojson_feature(fire)
    plume = _plume_to_geojson_feature(fire)
    if plume:
        result["plume"] = plume

    return result
