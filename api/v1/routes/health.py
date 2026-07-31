"""Liveness and readiness endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from api.dependencies import get_settings
from api.schemas.health import HealthResponse, HealthStatus
from core.config import Settings

router = APIRouter()
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.get("/live", response_model=HealthResponse, summary="Check API liveness")
def liveness(settings: SettingsDependency) -> HealthResponse:
    return HealthResponse(
        status=HealthStatus.OK,
        service=settings.app_name,
        version=settings.version,
    )


@router.get("/ready", response_model=HealthResponse, summary="Check API readiness")
def readiness(settings: SettingsDependency) -> HealthResponse:
    return HealthResponse(
        status=HealthStatus.READY,
        service=settings.app_name,
        version=settings.version,
        checks={"configuration": "ok"},
    )
