"""Liveness and readiness endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from api.dependencies import get_database, get_settings, get_task_broker
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
def readiness(
    request: Request,
    response: Response,
    settings: SettingsDependency,
) -> HealthResponse:
    checks: dict[str, str] = {}
    ready = True

    if settings.database_url is None:
        checks["database"] = "not_configured"
        ready = False
    else:
        try:
            database = get_database(request)
            checks["database"] = "ok" if database.check_connection() else "unavailable"
            ready = ready and checks["database"] == "ok"
        except Exception:
            checks["database"] = "unavailable"
            ready = False

    if settings.redis_url is None:
        checks["broker"] = "not_configured"
        ready = False
    else:
        try:
            broker = get_task_broker(request)
            checks["broker"] = "ok" if broker.client.ping() else "unavailable"
            ready = ready and checks["broker"] == "ok"
        except Exception:
            checks["broker"] = "unavailable"
            ready = False

    checks["task_capability"] = "shared" if settings.task_token_secret is not None else "ephemeral"
    checks["authentication"] = (
        "configured"
        if settings.auth_issuer and settings.auth_audience and settings.auth_jwks_url
        else "optional_anonymous"
    )
    if not ready:
        response.status_code = 503
    return HealthResponse(
        status=HealthStatus.READY if ready else HealthStatus.NOT_READY,
        service=settings.app_name,
        version=settings.version,
        checks=checks,
    )
