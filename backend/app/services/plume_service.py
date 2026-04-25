"""
Gaussian plume dispersion model for smoke trajectory estimation.

Generates a fan-shaped polygon representing predicted smoke spread
based on wind speed, direction, and atmospheric stability.
"""

import math
from shapely.geometry import Polygon


# ── Pasquill stability class constants ────────────────────────
# Using class D (neutral) as default — appropriate for most conditions
# sigma_y = a * x^b,  sigma_z = c * x^d  (x in km)
STABILITY_PARAMS = {
    "A": {"a": 0.22, "b": 0.894, "c": 0.20, "d": 0.894},   # Very unstable
    "B": {"a": 0.16, "b": 0.894, "c": 0.12, "d": 0.894},   # Unstable
    "C": {"a": 0.11, "b": 0.894, "c": 0.08, "d": 0.894},   # Slightly unstable
    "D": {"a": 0.08, "b": 0.894, "c": 0.06, "d": 0.894},   # Neutral
    "E": {"a": 0.06, "b": 0.894, "c": 0.03, "d": 0.894},   # Slightly stable
    "F": {"a": 0.04, "b": 0.894, "c": 0.016, "d": 0.894},  # Stable
}

# Earth radius for degree conversion
KM_PER_DEGREE_LAT = 111.0


def _km_to_degrees(km_north: float, km_east: float, lat: float) -> tuple[float, float]:
    """Convert km displacement to degree displacement at a given latitude."""
    delta_lat = km_north / KM_PER_DEGREE_LAT
    delta_lon = km_east / (KM_PER_DEGREE_LAT * math.cos(math.radians(lat)))
    return delta_lat, delta_lon


def calculate_gaussian_plume(
    lat: float,
    lon: float,
    wind_speed_kmh: float,
    wind_deg: float,
    duration_hours: float = 6.0,
    stability_class: str = "D",
    num_vertices: int = 16,
) -> Polygon:
    """
    Calculate a fan-shaped smoke plume polygon using Gaussian dispersion.

    Args:
        lat: Fire latitude
        lon: Fire longitude
        wind_speed_kmh: Wind speed in km/h
        wind_deg: Wind direction in meteorological degrees (0=N, 90=E, 180=S, 270=W)
                  This is the direction wind is COMING FROM.
                  Smoke travels in the OPPOSITE direction.
        duration_hours: How far ahead to project (default 6h)
        stability_class: Pasquill stability class A-F (default D = neutral)
        num_vertices: Number of vertices per side of the plume fan

    Returns:
        Shapely Polygon representing the estimated smoke plume area
    """
    # Minimum plume even with no wind (thermal convection)
    min_distance_km = 2.0

    # Distance smoke travels downwind
    distance_km = max(wind_speed_kmh * duration_hours, min_distance_km)

    # Cap at reasonable maximum (~500km in 6h = ~83 km/h winds)
    distance_km = min(distance_km, 500.0)

    # Wind direction: meteorological convention is where wind COMES FROM
    # Smoke goes in the OPPOSITE direction
    # Convert to math angle (0=East, counter-clockwise)
    smoke_direction_deg = (wind_deg + 180) % 360
    smoke_angle_rad = math.radians(90 - smoke_direction_deg)  # Convert to math convention

    # Get dispersion parameters for this stability class
    params = STABILITY_PARAMS.get(stability_class, STABILITY_PARAMS["D"])

    # Build the fan-shaped plume polygon
    # Points along the left edge, the tip, and the right edge
    vertices = []

    # Start at the fire origin
    vertices.append((lon, lat))

    for i in range(num_vertices + 1):
        # Distance along the plume axis (from 0 to full distance)
        fraction = i / num_vertices
        x_km = max(fraction * distance_km, 0.1)  # Avoid zero

        # Calculate crosswind spread (sigma_y) at this distance
        sigma_y = params["a"] * (x_km ** params["b"])

        # The plume width at this distance (2 sigma covers ~95% of spread)
        spread_km = 2.0 * sigma_y

        # Cap spread to something reasonable
        spread_km = min(spread_km, distance_km * 0.5)

        # Position along the centerline (in km from origin)
        center_north = x_km * math.sin(smoke_angle_rad)  # Flip for math convention
        center_east = x_km * math.cos(smoke_angle_rad)

        # Perpendicular direction for spread
        perp_angle = smoke_angle_rad + math.pi / 2

        # Left edge point
        left_north = center_north + spread_km * math.sin(perp_angle)
        left_east = center_east + spread_km * math.cos(perp_angle)
        dlat, dlon = _km_to_degrees(left_north, left_east, lat)
        vertices.append((lon + dlon, lat + dlat))

    # Now trace back along the right edge (reverse order)
    for i in range(num_vertices, -1, -1):
        fraction = i / num_vertices
        x_km = max(fraction * distance_km, 0.1)

        sigma_y = params["a"] * (x_km ** params["b"])
        spread_km = 2.0 * sigma_y
        spread_km = min(spread_km, distance_km * 0.5)

        center_north = x_km * math.sin(smoke_angle_rad)
        center_east = x_km * math.cos(smoke_angle_rad)

        perp_angle = smoke_angle_rad - math.pi / 2

        right_north = center_north + spread_km * math.sin(perp_angle)
        right_east = center_east + spread_km * math.cos(perp_angle)
        dlat, dlon = _km_to_degrees(right_north, right_east, lat)
        vertices.append((lon + dlon, lat + dlat))

    # Close the polygon
    vertices.append(vertices[0])

    return Polygon(vertices)
