"""
API v1 router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, items, tasks, prometheus, third_party_metrics, external_system

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(prometheus.router, prefix="/prometheus", tags=["prometheus"])
api_router.include_router(third_party_metrics.router, prefix="/third-party-metrics", tags=["third-party-metrics"])
api_router.include_router(external_system.router, prefix="/external-systems", tags=["external-systems"])