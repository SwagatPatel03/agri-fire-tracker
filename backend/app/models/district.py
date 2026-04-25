from sqlalchemy import Column, Integer, String, Float, Index
from geoalchemy2 import Geometry

from app.db.database import Base


class District(Base):
    """An administrative district of India with its geographic boundary."""

    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    state = Column(String, nullable=False)

    # Optional metadata
    area_sq_km = Column(Float, nullable=True)
    population = Column(Integer, nullable=True)

    # Stores the actual shape of the district boundary
    boundary = Column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326),
        nullable=False,
    )

    # Spatial index for fast containment queries
    __table_args__ = (
        Index("idx_district_boundary_gist", boundary, postgresql_using="gist"),
    )