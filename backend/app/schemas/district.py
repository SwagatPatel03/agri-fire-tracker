"""Pydantic schemas for district-related API responses."""

from pydantic import BaseModel


class DistrictRiskScore(BaseModel):
    """Risk score for a single district."""
    district: str
    state: str | None = None
    fire_count: int
    avg_frp: float | None = None
    max_frp: float | None = None
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL


class DistrictGeoJSON(BaseModel):
    """A district as a GeoJSON Feature."""
    type: str = "Feature"
    geometry: dict  # GeoJSON MultiPolygon
    properties: dict


class DistrictCollection(BaseModel):
    """GeoJSON FeatureCollection of districts."""
    type: str = "FeatureCollection"
    features: list[DistrictGeoJSON]
