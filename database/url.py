"""Database URL compatibility helpers."""


def sqlalchemy_database_url(database_url: str) -> str:
    """Select Psycopg 3 when a platform supplies a generic PostgreSQL URL."""
    for prefix in ("postgresql://", "postgres://"):
        if database_url.startswith(prefix):
            return database_url.replace(prefix, "postgresql+psycopg://", 1)
    return database_url
