from sqlalchemy import Column, Integer, String, Float, DateTime # To define the columns of our table
from geoalchemy2 import Geometry # To define the geometry column
from app.db.database import Base
from datetime import datetime

class Fire(Base):
    __tablename__ = "active_fires"

    id = Column(Integer, primary_key=True, index=True)

    # The 'Point' geometry type specifically for PostGIS
    location = Column(Geometry(geometry_type="POINT", srid=4326))
    """ In the world of mapping and corporate GIS, we can't just 
    store coordinates; we have to tell the database which "coordinate system" 
    we are using. 4326 is the industry standard for GPS (Latitude/Longitude)."""

    # The trajectory is the path the smoke is expected to take pre calculated 12 hours ago.
    trajectory = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)

    magnitude = Column(Float) # FRP - Fire Radiative Power
    wind_speed = Column(Float)
    wind_direction = Column(Float) # Degrees (0-360)

    detected_at = Column(DateTime, default=datetime.utcnow)
    district_name = Column(String, index=True) # To filter by adminstrative names    