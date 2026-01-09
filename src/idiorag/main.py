"""Main FastAPI application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import time

from fastapi import FastAPI, Request
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
    
    # Register custom chunkers
    logger.info("Registering custom chunkers...")
    from .rag.chunkers import register_chunker
    from examples.fishing.fishing_chunker import FishingLogChunker
    
    # Register with custom parameters
    register_chunker("fishing_log", lambda: FishingLogChunker(mode="hybrid", include_weather=True))
    logger.info("Registered fishing_log chunker with mode='hybrid', include_weather=True")
    
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
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all incoming requests with headers for debugging."""
        start_time = time.time()
        
        # Log request details
        logger.info(f"Incoming request: {request.method} {request.url.path}")
        logger.debug(f"   Query params: {dict(request.query_params)}")
        logger.debug(f"   Client: {request.client.host if request.client else 'unknown'}")
        
        # Log headers (especially Authorization)
        auth_header = request.headers.get("authorization", None)
        if auth_header:
            if auth_header.startswith("Bearer "):
                token_preview = auth_header[7:57]  # Show first 50 chars after "Bearer "
                logger.info(f"   Authorization header present: Bearer {token_preview}...")
            else:
                logger.warning(f"   Authorization header present but not Bearer format: {auth_header[:50]}")
        else:
            logger.warning(f"   No Authorization header found")
        
        # Log other relevant headers
        content_type = request.headers.get("content-type")
        if content_type:
            logger.debug(f"   Content-Type: {content_type}")
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            logger.info(f"Response: {response.status_code} ({process_time:.3f}s)")
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request failed: {type(e).__name__}: {str(e)} ({process_time:.3f}s)")
            raise
    
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
