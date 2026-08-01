"""Liveness and readiness endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from api.dependencies import get_settings
from api.schemas.health import HealthResponse, HealthStatus
from core.config import Settings
from database.session import Database
from workers.broker import build_broker

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
def readiness(response: Response, settings: SettingsDependency) -> HealthResponse:
    checks: dict[str, str] = {}
    ready = True

    if settings.database_url is None:
        checks["database"] = "not_configured"
        ready = False
    else:
        database = Database(
            settings.require_database_url(),
            pool_size=1,
            pool_timeout_seconds=settings.database_pool_timeout_seconds,
        )
        try:
            checks["database"] = "ok" if database.check_connection() else "unavailable"
            ready = ready and checks["database"] == "ok"
        except Exception:
            checks["database"] = "unavailable"
            ready = False
        finally:
            database.dispose()

    if settings.redis_url is None:
        checks["broker"] = "not_configured"
        ready = False
    else:
        broker = build_broker(settings)
        try:
            checks["broker"] = "ok" if broker.client.ping() else "unavailable"
            ready = ready and checks["broker"] == "ok"
        except Exception:
            checks["broker"] = "unavailable"
            ready = False
        finally:
            broker.close()

    checks["task_capability"] = "shared" if settings.task_token_secret is not None else "ephemeral"
    if not ready:
        response.status_code = 503
    return HealthResponse(
        status=HealthStatus.READY if ready else HealthStatus.NOT_READY,
        service=settings.app_name,
        version=settings.version,
        checks=checks,
    )
