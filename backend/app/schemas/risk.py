from pydantic import BaseModel

class DistrictRiskScore(BaseModel):
    district: str
    risk_score: int

    