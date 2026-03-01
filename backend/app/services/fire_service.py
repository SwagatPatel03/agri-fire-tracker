import requests
import math
from datetime import datetime
from shapely.geometry import Point, Polygon
from celery import shared_task
import csv
from io import StringIO

# Import our database session, models, and settings
from app.db.database import SessionLocal
from app.models.fire import Fire
from app.core.config import settings

def calculate_plume(lat, lon, wind_speed_kmh, wind_deg):
    # Calculates the distance over 12 hours
    distance = wind_speed_kmh * 12

    # Convert degrees to radians for Python's math functions
    angle = math.radians(wind_deg)

    # Calculate new coordinates
    new_lat = lat + distance * math.cos(angle)
    new_lon = lon + distance * math.sin(angle)

    return Polygon([(lon, lat), (new_lon, lat), (new_lon, new_lat)])

@shared_task
def fetch_and_process_nasa_fires():
    """
    Background job to fetch NASA fires, get weather data,
    calculate smoke plumes, and save to PostGIS.
    """
    db = SessionLocal()

    try:
        # 1. FETCH: We fetch the data from NASA's Firms API
        nasa_url = f"https://firms.eosdis.nasa.gov/api/country/csv/{settings.NASA_FIRMS_API_KEY}/IND/1"
        response = requests.get(nasa_url)

        # If NASA's servers are down or API key is down, stop the task safely
        if response.status_code != 200:
            print(f"NASA API Error: {response.status_code} - {response.text}")
            return

        # NASA returns raw CSV text. We have to convert it into a readble stream for Python
        csv_stream = StringIO(response.text)
        csv_reader = csv.DictReader(csv_stream) # Reads the CSV and treats each row as a dictionary

        # A simple in-memory dictionary to cache weather requests
        # Key: "lat,lon" Value: {"speed": 10, "deg": 270}
        weather_cache = {}

        for row in csv_reader:
            lat = float(row["latitude"]) # convert string to float
            lon = float(row["longitude"])
            frp = float(row["frp"])
            
            # NASA FIRMS CSVs split data and time into 'acq_date' (YYYY-MM-DD) and 'acq_time' (HHMM)
            # We need to stich them back together into proper datetime object
            acq_date = row["acq_date"] # e.g. "2026-03-01"
            acq_time = row["acq_time"].zfill(4) # Ensures time is always 4 didgits (e.g. 123 -> 0123)

            # Convert the stitched string into a Python datetime object
            fire_time = datetime.strptime(f"{acq_date} {acq_time}", "%Y-%m-%d %H%M")

            # IDEMPOTENCY CHECK: Does this fire already exist?
            # We check if a fire exists at this exact time and location
            existing_fire = db.query(Fire).filter(
                Fire.detected_at == fire_time,
                Fire.magnitude == frp
            ).first()

            if existing_fire:
                continue # Skip to the next fire if we already saved this one

            # ENRICH: Get weather Data with Caching
            # We round coordinates to 1 decimal place (~11 km resolution) for the cache key
            cache_key = f"{round(lat, 1)},{round(lon, 1)}"

            if cache_key in weather_cache:
                wind_speed, wind_deg = weather_cache[cache_key]
            else:
                # Actually call the OpenWeather API if not in cache
                weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={settings.OPEN_WEATHER_MAP_API_KEY}&units=metric"
                response = requests.get(weather_url)

                if response.status_code == 200:
                    weather_json = response.json()
                    wind_speed = weather_json['wind'].get('speed', 0) * 3.6 # Convert m/s to km/h
                    wind_deg = weather_json['wind'].get('deg', 0)
                    # Save cache for the next fire in this loop
                    weather_cache[cache_key] = (wind_speed, wind_deg)
                else:
                    wind_speed, wind_deg = 0, 0 # Fallback to 0 if API fails

            # CALCULATE: Generate the Shapely Plume Polygon
            plume_polygon = calculate_plume(lat, lon, wind_speed, wind_deg)
            fire_point = Point(lon, lat)

            # SAVE: Convert to WKT (Well-Known Text) and save to databases
            new_fire = Fire(
                location = f"SRID=4326;{fire_point.wkt}",
                trajectory = f"SRID=4326;{plume_polygon.wkt}",
                magnitude = frp,
                wind_speed = wind_speed,
                wind_direction = wind_deg,
                detected_at = fire_time,
                # In a full app, we would do a spatial query here to find the district name automatically
                # For now, we use "Unknown" as a fallback
                district_name = "Unknown"
            )

            db.add(new_fire)

        # Commit all the new fires to the database at once
        db.commit()

    except Exception as e:
        print(f"Error processing fires: {e}")
        db.rollback()
    finally:
        # Closing to prevent memory leaks
        db.close()