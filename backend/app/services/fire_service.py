from shapely import distance
import math
from shapely.geometry import Point, Polygon

def calculate_plume(lat, lon, wind_speed_kmh, wind_deg):

    # Calculates the distance over 12 hours
    distance = wind_speed_kmh * 12

    # Conver degree to radians for Python's math functions
    angle = math.radians(wind_deg)

    # Calculate new coordinates
    new_lat = lat + distance * math.cos(angle)
    new_lon = lon + distance * math.sin(angle)

    return Polygon([(lon, lat), (new_lon, lat), (new_lon, new_lat)])
    