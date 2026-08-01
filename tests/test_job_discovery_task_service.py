from api.schemas.job_search import JobSearchRequest
from api.services.job_discovery_tasks import JobDiscoveryTaskService
from api.services.task_capability import TaskCapability
from database.base import Base
from database.repositories.task_outbox import TaskOutboxRepository
from database.session import Database
from models.enums import BackgroundTaskStatus


class RecordingPublisher:
    def __init__(self):
        self.messages = []

    def enqueue(self, *, actor_name, task_id):
        self.messages.append((actor_name, task_id))


def test_service_commits_outbox_publishes_and_capability_scopes_cancellation():
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    publisher = RecordingPublisher()
    service = JobDiscoveryTaskService(
        database=database,
        publisher=publisher,
        capability=TaskCapability(b"x" * 32),
        max_attempts=4,
    )

    snapshot, token = service.create(
        request=JobSearchRequest(role="AI Engineer", location="India"),
        idempotency_key="service-outbox-intent",
    )

    assert snapshot.task.status == BackgroundTaskStatus.QUEUED
    assert publisher.messages == [("job_discovery", snapshot.task.id)]
    with database.session() as session:
        assert TaskOutboxRepository(session).get_pending_for_task(snapshot.task.id) is None

    assert service.cancel(task_id=snapshot.task.id, token="wrong-token") is None
    cancelled = service.cancel(task_id=snapshot.task.id, token=token)
    assert cancelled is not None
    assert cancelled.task.status == BackgroundTaskStatus.CANCELLED
    loaded = service.get(task_id=snapshot.task.id, token=token)
    assert loaded is not None
    assert loaded.task.status == BackgroundTaskStatus.CANCELLED
    assert loaded.outcome is None
