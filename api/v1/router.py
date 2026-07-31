"""Version 1 router composition."""

from fastapi import APIRouter

from api.v1.routes.health import router as health_router
from api.v1.routes.jobs import router as jobs_router
from api.v1.routes.recommendations import router as recommendations_router
from api.v1.routes.resumes import router as resumes_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(
    recommendations_router,
    prefix="/recommendations",
    tags=["recommendations"],
)
api_router.include_router(resumes_router, prefix="/resumes", tags=["resumes"])
