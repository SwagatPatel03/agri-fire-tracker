"""District API endpoints — boundaries, risk scores, and choropleth data."""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.shape import to_shape

from app.db.database import get_db
from app.models.fire import Fire
from app.models.district import District

router = APIRouter()


def _classify_risk(fire_count: int) -> str:
    """Classify risk level based on fire count."""
    if fire_count >= 50:
        return "CRITICAL"
    elif fire_count >= 25:
        return "HIGH"
    elif fire_count >= 10:
        return "MEDIUM"
    elif fire_count >= 3:
        return "LOW"
    return "NONE"


@router.get("/districts/risk-scores")
def get_district_risk_scores(
    hours: int = Query(24, ge=1, le=240, description="Time window in hours"),
    db: Session = Depends(get_db),
):
    """
    Compute fire risk scores per district using PostGIS spatial join.
    Returns districts sorted by risk (highest first).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    results = db.query(
        District.name,
        District.state,
        func.count(Fire.id).label("fire_count"),
        func.coalesce(func.avg(Fire.magnitude), 0).label("avg_frp"),
        func.coalesce(func.max(Fire.magnitude), 0).label("max_frp"),
    ).outerjoin(
        Fire,
        func.ST_Contains(District.boundary, Fire.location)
        & (Fire.detected_at >= cutoff)
        & (Fire.is_active == True),  # noqa: E712
    ).group_by(
        District.name, District.state,
    ).having(
        func.count(Fire.id) > 0,
    ).order_by(
        func.count(Fire.id).desc(),
    ).all()

    return [
        {
            "district": row.name,
            "state": row.state,
            "fire_count": row.fire_count,
            "avg_frp": round(float(row.avg_frp), 2) if row.avg_frp else 0,
            "max_frp": round(float(row.max_frp), 2) if row.max_frp else 0,
            "risk_level": _classify_risk(row.fire_count),
        }
        for row in results
    ]


@router.get("/districts")
def get_districts(
    db: Session = Depends(get_db),
):
    """Return all district boundaries as GeoJSON for choropleth rendering."""
    districts = db.query(District).all()

    features = []
    for d in districts:
        shape = to_shape(d.boundary)
        # Convert MultiPolygon to GeoJSON-compatible coordinates
        coords = []
        for polygon in shape.geoms:
            exterior = list(polygon.exterior.coords)
            holes = [list(hole.coords) for hole in polygon.interiors]
            coords.append([exterior] + holes)

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": coords,
            },
            "properties": {
                "name": d.name,
                "state": d.state,
                "area_sq_km": d.area_sq_km,
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {"count": len(features)},
    }


@router.get("/districts/{name}")
def get_district_detail(
    name: str,
    hours: int = Query(24, ge=1, le=240),
    db: Session = Depends(get_db),
):
    """Get a specific district with its active fires."""
    district = db.query(District).filter(District.name == name).first()
    if not district:
        return {"error": "District not found"}

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    fire_count = db.query(func.count(Fire.id)).filter(
        func.ST_Contains(District.boundary, Fire.location),
        Fire.detected_at >= cutoff,
        Fire.is_active == True,  # noqa: E712
    ).scalar()

    return {
        "name": district.name,
        "state": district.state,
        "area_sq_km": district.area_sq_km,
        "fire_count": fire_count,
        "risk_level": _classify_risk(fire_count),
    }
