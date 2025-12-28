"""Main FastAPI application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .logging_config import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    
    Yields:
        None
    """
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    
    # Startup: Initialize connections, load models, etc.
    from .database import init_db, close_db
    
    logger.info("Initializing database connections...")
    await init_db()
    
    # TODO: Initialize LlamaIndex
    # TODO: Load embedding model
    
    yield
    
    # Shutdown: Close connections, cleanup resources
    logger.info("Shutting down application")
    await close_db()


def create_application() -> FastAPI:
    """Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description="API-first RAG framework with user-isolated queries",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routers
    from .api import api_router
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check() -> JSONResponse:
        """Health check endpoint.
        
        Returns:
            JSONResponse: Application health status
        """
        return JSONResponse(
            content={
                "status": "healthy",
                "app_name": settings.app_name,
                "version": settings.app_version,
                "environment": settings.environment,
            }
        )
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root() -> JSONResponse:
        """Root endpoint.
        
        Returns:
            JSONResponse: Basic application information
        """
        return JSONResponse(
            content={
                "app": settings.app_name,
                "version": settings.app_version,
                "docs": "/docs",
                "health": "/health",
            }
        )
    
    return app


# Create application instance
app = create_application()
