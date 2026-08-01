"""Construct the background-job broker without connecting during application import."""

from dramatiq.brokers.redis import RedisBroker

from core.config import Settings, settings


def build_broker(app_settings: Settings | None = None) -> RedisBroker:
    """Build a namespaced Redis broker for an explicit worker runtime."""
    active_settings = app_settings or settings
    return RedisBroker(
        url=active_settings.require_redis_url(),
        namespace=active_settings.worker_broker_namespace,
    )
