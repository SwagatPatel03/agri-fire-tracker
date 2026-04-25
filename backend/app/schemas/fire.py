"""Pydantic schemas for fire-related API responses."""

from datetime import datetime
from pydantic import BaseModel


class FireFeatureProperties(BaseModel):
    """Properties for a fire GeoJSON feature."""
    id: int
    magnitude: float
    confidence: str | None
    satellite: str | None
    wind_speed: float
    wind_direction: float
    detected_at: datetime
    district_name: str
    is_active: bool


class FireGeoJSON(BaseModel):
    """A single fire as a GeoJSON Feature."""
    type: str = "Feature"
    geometry: dict  # GeoJSON Point
    properties: FireFeatureProperties


class FireCollection(BaseModel):
    """GeoJSON FeatureCollection of fires."""
    type: str = "FeatureCollection"
    features: list[FireGeoJSON]


class PlumeGeoJSON(BaseModel):
    """A smoke plume as a GeoJSON Feature."""
    type: str = "Feature"
    geometry: dict  # GeoJSON Polygon
    properties: dict


class PlumeCollection(BaseModel):
    """GeoJSON FeatureCollection of plumes."""
    type: str = "FeatureCollection"
    features: list[PlumeGeoJSON]
