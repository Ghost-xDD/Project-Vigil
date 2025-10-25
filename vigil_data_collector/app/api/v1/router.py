from fastapi import APIRouter
from app.api.v1.endpoints import metrics

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])

