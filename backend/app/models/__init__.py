# Import all models here so Alembic can discover them
from app.models.fire import Fire
from app.models.district import District
from app.models.alert import Alert

__all__ = ["Fire", "District", "Alert"]
