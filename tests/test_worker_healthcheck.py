from unittest.mock import Mock

from workers import healthcheck


def test_worker_healthcheck_probes_database_and_broker(monkeypatch):
    database = Mock()
    database.check_connection.return_value = True
    broker = Mock()
    broker.client.ping.return_value = True
    settings = Mock()
    settings.require_database_url.return_value = "sqlite://"
    settings.database_pool_timeout_seconds = 2

    monkeypatch.setattr(healthcheck, "Database", Mock(return_value=database))
    monkeypatch.setattr(healthcheck, "build_broker", Mock(return_value=broker))

    assert healthcheck.is_worker_ready(settings) is True
    database.dispose.assert_called_once_with()
    broker.close.assert_called_once_with()


def test_worker_healthcheck_fails_closed_and_releases_resources(monkeypatch):
    database = Mock()
    database.check_connection.side_effect = RuntimeError("unavailable")
    broker = Mock()
    settings = Mock()
    settings.require_database_url.return_value = "sqlite://"
    settings.database_pool_timeout_seconds = 2

    monkeypatch.setattr(healthcheck, "Database", Mock(return_value=database))
    monkeypatch.setattr(healthcheck, "build_broker", Mock(return_value=broker))

    assert healthcheck.is_worker_ready(settings) is False
    database.dispose.assert_called_once_with()
    broker.close.assert_called_once_with()
