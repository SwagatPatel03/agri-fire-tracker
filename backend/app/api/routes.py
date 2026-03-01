# APIRouter - used to create a router for the API
# Depends - used to inject dependencies
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
# func - used to perform database functions
from sqlalchemy import func
from app.db.database import get_db
from app.models.fire import Fire
from app.models.district import District

# Create a router for the API
router = APIRouter()

@router.get("/districts/risk-scores")
# db - Name of the parameter
# :Session - db is an instance of SQLAchemy session
# Depends - FastAPI dependency injection
def get_district_risk_scores(db: Session = Depends(get_db)):
    # 1. Ask PostGIS to find which District contains which Fire
    # 2. GROUP BY district name
    # 3. COUNT the number of fires

    results = db.query(
        District.name,
        func.count(Fire.id).label("active_fire_count")
    ).filter(
        # The spatial containment check - if fire is present inside district
        func.ST_Contains(District.boundary, Fire.location)
    ).group_by(
        District.name
    ).order_by(
        func.count(Fire.id).desc() # Puts highest risk at top
    ).all()

    # Format the results into a list of dictionariries for the frontend.
    return [{"district": row.name, "risk_score": row.active_fire_count} for row in results]



    