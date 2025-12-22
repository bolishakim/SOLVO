"""
Core App Routers

API endpoints for core application functionality.
"""

from app.core.routers.auth import router as auth_router

__all__ = [
    "auth_router",
]
