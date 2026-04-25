"""Weather data service using Open-Meteo (free, no API key required)."""

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Reusable HTTP client with connection pooling
_client = httpx.Client(timeout=10.0)

# Grid resolution for weather cache (~55km cells)
# India covers roughly 30x32 degrees = ~60x64 grid = ~3,840 cells max
_GRID_RESOLUTION = 0.5


def _snap_to_grid(val: float) -> float:
    """Snap a coordinate to the nearest grid point."""
    return round(val / _GRID_RESOLUTION) * _GRID_RESOLUTION


def get_wind_data(lat: float, lon: float, cache: dict | None = None) -> tuple[float, float]:
    """
    Fetch current wind speed and direction for a coordinate.

    Uses coordinate snapping to a 0.5° grid (~55km) for cache efficiency.
    With ~15,000 fire points across India, this reduces API calls from
    ~15,000 down to ~500-1,500.

    Args:
        lat: Latitude
        lon: Longitude
        cache: Optional dict for in-memory caching across calls

    Returns:
        (wind_speed_kmh, wind_direction_deg)
    """
    grid_lat = _snap_to_grid(lat)
    grid_lon = _snap_to_grid(lon)
    cache_key = f"{grid_lat},{grid_lon}"

    if cache is not None and cache_key in cache:
        return cache[cache_key]

    try:
        response = _client.get(
            settings.OPEN_METEO_BASE_URL,
            params={
                "latitude": grid_lat,
                "longitude": grid_lon,
                "current": "wind_speed_10m,wind_direction_10m",
            },
        )
        response.raise_for_status()

        data = response.json()
        current = data.get("current", {})

        # Open-Meteo returns wind_speed in km/h by default
        wind_speed = current.get("wind_speed_10m", 0.0)
        wind_deg = current.get("wind_direction_10m", 0.0)

        result = (float(wind_speed), float(wind_deg))

        if cache is not None:
            cache[cache_key] = result

        return result

    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.warning(f"Weather fetch failed for ({grid_lat}, {grid_lon}): {e}")
        return (0.0, 0.0)
