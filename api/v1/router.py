"""Version 1 router composition."""

from fastapi import APIRouter

from api.v1.routes.applications import router as applications_router
from api.v1.routes.health import router as health_router
from api.v1.routes.auth import router as auth_router
from api.v1.routes.jobs import router as jobs_router
from api.v1.routes.recommendations import router as recommendations_router
from api.v1.routes.reminders import router as reminders_router
from api.v1.routes.resumes import router as resumes_router
from api.v1.routes.saved_jobs import router as saved_jobs_router

api_router = APIRouter()
api_router.include_router(
    applications_router,
    prefix="/applications",
    tags=["applications"],
)
api_router.include_router(reminders_router, prefix="/reminders", tags=["reminders"])
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(
    recommendations_router,
    prefix="/recommendations",
    tags=["recommendations"],
)
api_router.include_router(resumes_router, prefix="/resumes", tags=["resumes"])
api_router.include_router(
    saved_jobs_router,
    prefix="/saved-jobs",
    tags=["saved jobs"],
)
