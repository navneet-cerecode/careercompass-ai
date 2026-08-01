"""Publish one maintenance cycle for an external scheduler."""

from core.config import settings
from workers.broker import build_broker
from workers.publisher import BackgroundTaskPublisher


def main() -> None:
    broker = build_broker(settings)
    try:
        BackgroundTaskPublisher(
            broker,
            queue_name=settings.worker_queue_name,
        ).enqueue_maintenance()
    finally:
        broker.close()


if __name__ == "__main__":
    main()
