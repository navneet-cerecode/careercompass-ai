"""Live Redis integration gate for the worker broker."""

import os

import pytest

from core.config import Settings
from workers.broker import build_broker


@pytest.mark.redis
def test_redis_broker_connects_with_explicit_test_url():
    redis_url = os.getenv("TEST_REDIS_URL")
    if redis_url is None:
        pytest.skip("TEST_REDIS_URL is required for the Redis integration gate.")

    broker = build_broker(
        Settings(
            _env_file=None,
            redis_url=redis_url,
            worker_broker_namespace="careercompass_test",
        )
    )
    try:
        assert broker.client.ping() is True
        assert broker.namespace == "careercompass_test"
    finally:
        broker.close()
