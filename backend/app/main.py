from fastapi import FastAPI
# CORS - Cross Origin Resource Sharing - allows the frontend to talk to the backend
from fastapi.middleware.cors import CORSMiddleware

# Import the database engine and Base to create tables
from app.db.database import engine, Base

# Import our API routes
from app.api import routes

# 1. Initialize Database Tables
# This tells SQLAlchemy to check PostGIS and create the 'active_fires'
# and 'districts' tables if they don't already exist.
Base.metadata.create_all(bind=engine)

# 2. Initialize the FastAPI App
app = FastAPI(
    title="Agri-Fire API",
    description="Backend for the Thermal Tracking & Smog Prediction Grid",
    version="1.0.0"
)

# 3. Configure CORS (Cross-Origin Resource Sharing)
# Since we will be building the frontend in React, the browser will block
# requests to this API unless we explicitly allow them.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Will restrict this to our exact React URL (e.g., http://localhost:3000)
    allow_credentials=True,
    allow_methods=["*"], # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allows all headers
)

# 4. Register the API Routes
# We attach the router we built earlier. Adding a prefix is a standard
# API practice so our URL looks like : api/v1/districts/risk-scores
app.include_router(routes.router, prefix="/api/v1", tags=["Districts"])

# 5. Root Health Check
@app.get("/", tags=["System"])
def root():
    return {
        "status": "online",
        "message": "Agri-Fire API is actively monitoring."
    }