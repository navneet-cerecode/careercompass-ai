from unittest.mock import patch

import pytest

from core.config import Settings
from workers.broker import build_broker


def test_build_broker_requires_explicit_redis_configuration():
    with pytest.raises(
        ValueError,
        match="REDIS_URL is required for background workers",
    ):
        build_broker(Settings(_env_file=None, redis_url=None))


def test_build_broker_uses_secret_url_and_namespace():
    app_settings = Settings(
        _env_file=None,
        redis_url="redis://:secret@redis.internal:6379/2",
        worker_broker_namespace="careercompass_test",
    )

    with patch("workers.broker.RedisBroker") as broker_type:
        broker = build_broker(app_settings)

    assert broker is broker_type.return_value
    broker_type.assert_called_once_with(
        url="redis://:secret@redis.internal:6379/2",
        namespace="careercompass_test",
    )
