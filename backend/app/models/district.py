from sqlalchemy import Column, Integer, String
from geoalchemy2 import Geometry
from app.db.database import Base

class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    state = Column(String)

    # Stores the actual shape of the district
    boundary = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326))