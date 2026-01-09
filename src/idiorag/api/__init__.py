"""API v1 router aggregator."""

from fastapi import APIRouter

from .endpoints import documents, query

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["Documents"]
)

api_router.include_router(
    query.router,
    prefix="/query",
    tags=["Query"]
)
