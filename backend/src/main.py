"""Main FastAPI application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import settings
from .database.connection import create_database_engine, get_database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting VILS Backend...")

    # Initialize database
    engine = create_database_engine()
    app.state.db_engine = engine

    # Validate configuration in production
    if settings.environment == "production":
        assert settings.secret_key != "dev-secret-key"
        assert not settings.debug
        
    print("✅ VILS Backend started successfully!")

    yield

    # Shutdown
    print("🛑 Shutting down VILS Backend...")
    if hasattr(app.state, "db_engine"):
        app.state.db_engine.dispose()
    print("✅ VILS Backend shutdown complete!")


# Initialize Sentry if DSN is provided
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(auto_enabling_integrations=False),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        environment=settings.environment,
    )

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Version Issue Locator API",
    description="""
    ## Overview
    
    The Version Issue Locator System (VILS) helps development teams identify 
    problematic code versions using binary search methodology. The system 
    integrates with third-party build and testing services.
    
    ## Features
    
    * **Binary Search Algorithm**: Efficiently narrow down problematic commits
    * **Third-party Integration**: Works with Jenkins, GitHub Actions, GitLab CI
    * **Task Management**: Track and manage issue localization sessions
    * **Real-time Updates**: WebSocket support for live build status
    
    ## Authentication
    
    This API uses JWT Bearer token authentication. Obtain a token via 
    `/api/auth/login` and include it in the Authorization header: `Bearer <token>`
    """,
    version="1.0.0",
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    lifespan=lifespan,
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["vils.example.com"]
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Health check endpoints
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/ready")
async def readiness_check() -> dict:
    """Readiness check endpoint."""
    # Check database connection
    try:
        db = get_database()
        # Simple query to verify database connectivity
        await db.execute("SELECT 1")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "error": str(e)}
        )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        generate_latest(),
        media_type="text/plain; charset=utf-8"
    )


# Import and include routers (will be added as we create them)
# from .api.auth import router as auth_router
# from .api.projects import router as projects_router
# from .api.tasks import router as tasks_router
# from .api.builds import router as builds_router

# app.include_router(auth_router, prefix=f"{settings.api_prefix}/auth", tags=["Authentication"])
# app.include_router(projects_router, prefix=f"{settings.api_prefix}/projects", tags=["Projects"])
# app.include_router(tasks_router, prefix=f"{settings.api_prefix}/tasks", tags=["Tasks"])
# app.include_router(builds_router, prefix=f"{settings.api_prefix}/builds", tags=["Builds"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )