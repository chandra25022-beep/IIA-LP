"""
FastAPI Application Entry Point
IIA Project: Identification of Uninsured Vehicles
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .api import vehicle_router, reports_router, integration_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IIA Vehicle Integration System",
    description=(
        "Information Integration system for identifying uninsured vehicles. "
        "Integrates 5 independently designed databases via Mediation/Federated architecture."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for frontend — allow all origins so LAN peers can access
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,   # must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(vehicle_router)
app.include_router(reports_router)
app.include_router(integration_router)


@app.on_event("startup")
async def startup_event():
    logger.info("IIA Vehicle Integration System starting up...")
    logger.info("Initializing 5 independent data sources...")


@app.get("/")
async def root():
    return {
        "message": "IIA Vehicle Integration System API",
        "docs": "/docs",
        "health": "/api/health",
    }
