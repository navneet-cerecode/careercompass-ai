"""Container health probe for the background worker."""

from core.config import Settings, settings
from database.session import Database
from workers.broker import build_broker


def is_worker_ready(app_settings: Settings = settings) -> bool:
    """Return whether the worker's required database and broker are reachable."""
    database: Database | None = None
    broker = None
    try:
        database = Database(
            app_settings.require_database_url(),
            pool_size=1,
            pool_timeout_seconds=app_settings.database_pool_timeout_seconds,
        )
        broker = build_broker(app_settings)
        return database.check_connection() and bool(broker.client.ping())
    except Exception:
        return False
    finally:
        if broker is not None:
            broker.close()
        if database is not None:
            database.dispose()


def main() -> None:
    raise SystemExit(0 if is_worker_ready() else 1)


if __name__ == "__main__":
    main()
