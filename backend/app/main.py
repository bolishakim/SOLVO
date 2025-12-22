"""
Landfill Management System - Main Application

FastAPI application entry point with health endpoints and middleware configuration.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import check_database_connection, close_db, create_schemas
from app.shared.exceptions import AppException
from app.shared.responses import ErrorCodes
from app.core.routers import auth_router
from app.core.routers.admin import router as admin_router
from app.middleware import (
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
)


# ═══════════════════════════════════════════════════════════
# LIFESPAN MANAGEMENT
# ═══════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management.

    Handles startup and shutdown events.
    """
    # ─── Startup ───────────────────────────────────────────
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Debug mode: {settings.DEBUG}")

    # Create database schemas if they don't exist
    try:
        await create_schemas()
        print("Database schemas verified/created")
    except Exception as e:
        print(f"Warning: Could not create schemas: {e}")

    yield

    # ─── Shutdown ──────────────────────────────────────────
    print("Shutting down application...")
    await close_db()
    print("Database connections closed")


# ═══════════════════════════════════════════════════════════
# EXCEPTION HANDLERS
# ═══════════════════════════════════════════════════════════

def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers for the application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """
        Handle application-specific exceptions.

        All AppException subclasses are caught here and converted to JSON responses.
        """
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handle Pydantic validation errors from request bodies/params.

        Converts validation errors to standardized error response format.
        """
        # Extract field errors
        errors = {}
        for error in exc.errors():
            loc = error.get("loc", [])
            # Skip 'body' prefix in location
            field = ".".join(str(l) for l in loc if l != "body")
            errors[field] = error.get("msg", "Invalid value")

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": ErrorCodes.VALIDATION_ERROR,
                    "message": "Request validation failed",
                    "details": {"fields": errors},
                },
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Global exception handler for unhandled errors.

        In production, this prevents leaking internal error details.
        """
        if settings.DEBUG:
            # In debug mode, show full error details
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": ErrorCodes.INTERNAL_ERROR,
                        "message": str(exc),
                        "details": {"type": type(exc).__name__},
                    },
                },
            )
        else:
            # In production, hide internal details
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": ErrorCodes.INTERNAL_ERROR,
                        "message": "An unexpected error occurred",
                    },
                },
            )


# ═══════════════════════════════════════════════════════════
# APPLICATION FACTORY
# ═══════════════════════════════════════════════════════════

def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
        ## Landfill Management System API

        Multi-workflow backend system for Austrian waste management company.

        ### Features:
        - **Authentication**: JWT-based auth with 2FA support
        - **User Management**: Role-based access control (Admin, Standard User, Viewer)
        - **Audit Logging**: Complete tracking of all user actions
        - **Workflows**: Modular workflow system starting with Landfill Document Management

        ### Schemas:
        - `core_app`: Authentication, users, sessions, audit logs
        - `landfill_mgmt`: Construction sites, weigh slips, hazardous slips
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ─── Custom Middleware ─────────────────────────────────
    # Note: Middleware executes in REVERSE order of addition
    # So we add them bottom-up: last added = first executed

    # 3. Rate Limiting (runs third, after request ID and security headers)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=60,
        auth_requests_per_minute=10,
    )

    # 2. Security Headers (runs second)
    app.add_middleware(
        SecurityHeadersMiddleware,
        hsts_enabled=not settings.DEBUG,  # Disable HSTS in debug mode
    )

    # 1. Request ID (runs first - assigns ID to each request)
    app.add_middleware(RequestIDMiddleware)

    # ─── CORS Middleware ───────────────────────────────────
    # CORS needs to be added last (so it runs first, before our middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    )

    # ─── Exception Handlers ────────────────────────────────
    register_exception_handlers(app)

    # ─── Register Routers ──────────────────────────────────
    # Core routers
    app.include_router(
        auth_router,
        prefix=f"{settings.API_PREFIX}/auth",
        tags=["Authentication"],
    )
    app.include_router(
        admin_router,
        prefix=settings.API_PREFIX,
        tags=["Admin"],
    )

    # Workflow routers (will be added later)
    # register_workflows(app)

    return app


# Create application instance
app = create_application()


# ═══════════════════════════════════════════════════════════
# HEALTH CHECK ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.get(
    "/health",
    tags=["Health"],
    summary="Basic health check",
    response_description="Application health status",
)
async def health_check() -> dict[str, Any]:
    """
    Basic health check endpoint.

    Returns application status and metadata.
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get(
    "/health/db",
    tags=["Health"],
    summary="Database health check",
    response_description="Database connection status",
)
async def health_check_db() -> dict[str, Any]:
    """
    Database health check endpoint.

    Verifies database connectivity.
    """
    db_healthy = await check_database_connection()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database_connected": db_healthy,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get(
    "/",
    tags=["Root"],
    summary="API root",
    include_in_schema=False,
)
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


# ═══════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
