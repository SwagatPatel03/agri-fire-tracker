from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging, get_logger
from app.api import fires, districts, alerts, system

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the application."""
    setup_logging()
    logger.info("Agri-Fire API starting up")
    yield
    logger.info("Agri-Fire API shutting down")


app = FastAPI(
    title="Agri-Fire API",
    description="Backend for the Thermal Tracking & Smog Prediction Grid",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — restrict in production, open for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(fires.router,     prefix="/api/v1", tags=["Fires"])
app.include_router(districts.router, prefix="/api/v1", tags=["Districts"])
app.include_router(alerts.router,    prefix="/api/v1", tags=["Alerts"])
app.include_router(system.router,    prefix="/api/v1", tags=["System"])


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "version": "2.0.0",
        "message": "Agri-Fire API is actively monitoring.",
    }