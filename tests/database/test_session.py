import pytest
from sqlalchemy import Column, Integer, MetaData, Table, insert, select

from database.session import Database


def make_database() -> tuple[Database, Table]:
    database = Database("sqlite+pysqlite:///:memory:")
    metadata = MetaData()
    records = Table(
        "records",
        metadata,
        Column("id", Integer, primary_key=True),
    )
    metadata.create_all(database.engine)
    return database, records


def test_database_session_commits_successful_transactions():
    database, records = make_database()

    with database.session() as session:
        session.execute(insert(records).values(id=1))

    with database.session() as session:
        assert session.execute(select(records.c.id)).scalar_one() == 1


def test_database_session_rolls_back_failed_transactions():
    database, records = make_database()

    with pytest.raises(RuntimeError):
        with database.session() as session:
            session.execute(insert(records).values(id=1))
            raise RuntimeError("synthetic failure")

    with database.session() as session:
        assert session.execute(select(records.c.id)).scalar_one_or_none() is None


def test_database_connection_health_check():
    database, _ = make_database()

    assert database.check_connection() is True
