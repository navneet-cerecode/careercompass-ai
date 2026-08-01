from datetime import UTC, datetime, timedelta

from api.schemas.job_search import JobSearchRequest
from core.config import Settings
from database.base import Base
from database.models.tasks import BackgroundTaskRecord
from database.models.job_discovery_tasks import JobDiscoveryTaskRecord
from database.models.tasks import TaskOutboxRecord
from database.repositories.job_discovery_tasks import JobDiscoveryTaskRepository
from database.repositories.task_outbox import TaskOutboxRepository
from database.repositories.tasks import BackgroundTaskRepository
from database.session import Database
from models.enums import BackgroundTaskStatus
from workers.maintenance import TaskMaintenance
from workers.outbox import TaskOutboxDispatcher


class RecordingPublisher:
    def __init__(self):
        self.messages = []

    def enqueue(self, *, actor_name, task_id):
        self.messages.append((actor_name, task_id))


def test_maintenance_recovers_stale_work_and_replays_outbox():
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    old = datetime.now(UTC) - timedelta(hours=1)
    with database.session() as session:
        task, _ = JobDiscoveryTaskRepository(session).create(
            request=JobSearchRequest(role="AI Engineer", location="India"),
            idempotency_key="maintenance-recovery",
            max_attempts=2,
        )
        pending = TaskOutboxRepository(session).get_pending_for_task(task.id)
        assert pending is not None
        TaskOutboxRepository(session).record_attempt(pending.id, published=True)
        BackgroundTaskRepository(session).start(task_id=task.id, user_id=None)
        record = session.get(BackgroundTaskRecord, task.id)
        assert record is not None
        record.heartbeat_at = old
        record.updated_at = old
        assert TaskOutboxRepository(session).get_pending_for_task(task.id) is None

    publisher = RecordingPublisher()
    settings = Settings(
        _env_file=None,
        task_stale_after_seconds=60,
        task_queue_expiry_seconds=600,
        task_retention_days=30,
    )
    result = TaskMaintenance(
        database=database,
        dispatcher=TaskOutboxDispatcher(database, publisher),
        settings=settings,
    ).run()

    assert result.requeued == 1
    assert result.published == 1
    assert publisher.messages == [("job_discovery", task.id)]
    with database.session() as session:
        recovered = BackgroundTaskRepository(session).get(task_id=task.id, user_id=None)
    assert recovered is not None
    assert recovered.status == BackgroundTaskStatus.QUEUED


def test_outbox_remains_pending_after_broker_failure():
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    with database.session() as session:
        task, _ = JobDiscoveryTaskRepository(session).create(
            request=JobSearchRequest(role="AI Engineer", location="India"),
            idempotency_key="outbox-broker-failure",
            max_attempts=2,
        )

    class FailingPublisher:
        def enqueue(self, **_):
            raise ConnectionError("broker unavailable")

    dispatcher = TaskOutboxDispatcher(database, FailingPublisher())
    try:
        dispatcher.dispatch_task(task.id)
    except ConnectionError:
        pass
    else:
        raise AssertionError("Expected broker failure.")

    with database.session() as session:
        pending = TaskOutboxRepository(session).get_pending_for_task(task.id)
    assert pending is not None
    assert pending.attempt_count == 1


def test_maintenance_purges_terminal_task_graph_after_retention():
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    now = datetime.now(UTC)
    with database.session() as session:
        task, _ = JobDiscoveryTaskRepository(session).create(
            request=JobSearchRequest(role="AI Engineer", location="India"),
            idempotency_key="retention-purge-task",
            max_attempts=2,
        )
        BackgroundTaskRepository(session).request_cancel(
            task_id=task.id,
            user_id=None,
        )
        record = session.get(BackgroundTaskRecord, task.id)
        assert record is not None
        record.finished_at = now - timedelta(days=2)

    result = TaskMaintenance(
        database=database,
        dispatcher=TaskOutboxDispatcher(database, RecordingPublisher()),
        settings=Settings(_env_file=None, task_retention_days=1),
    ).run(now=now)

    assert result.purged == 1
    with database.session() as session:
        assert session.get(BackgroundTaskRecord, task.id) is None
        assert session.get(JobDiscoveryTaskRecord, task.id) is None
        assert (
            session.query(TaskOutboxRecord)
            .filter(TaskOutboxRecord.task_id == task.id)
            .one_or_none()
            is None
        )
