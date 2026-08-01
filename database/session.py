"""Database engine and transaction lifecycle."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Database:
    """Own one SQLAlchemy engine and provide transaction-scoped sessions."""

    def __init__(
        self,
        database_url: str,
        *,
        pool_size: int = 5,
        pool_timeout_seconds: int = 10,
    ) -> None:
        engine_options: dict[str, object] = {"pool_pre_ping": True}
        if database_url.startswith("sqlite") and ":memory:" in database_url:
            engine_options.update(
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        elif not database_url.startswith("sqlite"):
            engine_options.update(
                pool_size=pool_size,
                pool_timeout=pool_timeout_seconds,
            )

        self.engine: Engine = create_engine(database_url, **engine_options)
        if database_url.startswith("sqlite"):
            event.listen(self.engine, "connect", self._enable_sqlite_foreign_keys)
        self._session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def check_connection(self) -> bool:
        with self.engine.connect() as connection:
            return connection.execute(text("SELECT 1")).scalar_one() == 1

    def dispose(self) -> None:
        self.engine.dispose()

    @staticmethod
    def _enable_sqlite_foreign_keys(dbapi_connection, _) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
