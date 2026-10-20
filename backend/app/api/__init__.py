# API package init
from .routes_vehicle import router as vehicle_router
from .routes_reports import router as reports_router
from .routes_integration import router as integration_router

__all__ = ["vehicle_router", "reports_router", "integration_router"]
