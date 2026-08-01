"""Transactional outbox for durable task publication."""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.tasks import BackgroundTaskRecord, TaskOutboxRecord
from models.enums import BackgroundTaskStatus


@dataclass(frozen=True)
class TaskOutboxMessage:
    id: UUID
    task_id: UUID
    actor_name: str
    attempt_count: int
    user_id: UUID | None


class TaskOutboxRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ensure(self, *, task_id: UUID, actor_name: str) -> TaskOutboxMessage:
        record = self.session.scalar(
            select(TaskOutboxRecord).where(TaskOutboxRecord.task_id == task_id)
        )
        if record is None:
            record = TaskOutboxRecord(task_id=task_id, actor_name=actor_name)
            self.session.add(record)
            self.session.flush()
        elif record.actor_name != actor_name:
            raise ValueError("Task outbox actor does not match the existing delivery.")
        return self._to_domain(record)

    def reset(self, *, task_id: UUID, actor_name: str) -> TaskOutboxMessage:
        message = self.ensure(task_id=task_id, actor_name=actor_name)
        record = self.session.get(TaskOutboxRecord, message.id)
        assert record is not None
        record.published_at = None
        self.session.flush()
        return self._to_domain(record)

    def get_pending_for_task(self, task_id: UUID) -> TaskOutboxMessage | None:
        row = self.session.execute(
            select(TaskOutboxRecord, BackgroundTaskRecord.user_id)
            .join(BackgroundTaskRecord, BackgroundTaskRecord.id == TaskOutboxRecord.task_id)
            .where(
                TaskOutboxRecord.task_id == task_id,
                TaskOutboxRecord.published_at.is_(None),
                BackgroundTaskRecord.status == BackgroundTaskStatus.QUEUED.value,
            )
        ).one_or_none()
        return self._to_domain(*row) if row is not None else None

    def list_pending(self, *, limit: int) -> tuple[TaskOutboxMessage, ...]:
        rows = self.session.execute(
            select(TaskOutboxRecord, BackgroundTaskRecord.user_id)
            .join(BackgroundTaskRecord, BackgroundTaskRecord.id == TaskOutboxRecord.task_id)
            .where(
                TaskOutboxRecord.published_at.is_(None),
                BackgroundTaskRecord.status == BackgroundTaskStatus.QUEUED.value,
            )
            .order_by(TaskOutboxRecord.created_at, TaskOutboxRecord.id)
            .limit(limit)
        ).all()
        return tuple(self._to_domain(*row) for row in rows)

    def record_attempt(self, message_id: UUID, *, published: bool) -> None:
        record = self.session.get(TaskOutboxRecord, message_id)
        if record is None:
            return
        now = datetime.now(timezone.utc)
        record.attempt_count += 1
        record.last_attempt_at = now
        if published:
            record.published_at = now
        self.session.flush()

    @staticmethod
    def _to_domain(
        record: TaskOutboxRecord,
        user_id: UUID | None = None,
    ) -> TaskOutboxMessage:
        return TaskOutboxMessage(
            id=record.id,
            task_id=record.task_id,
            actor_name=record.actor_name,
            attempt_count=record.attempt_count,
            user_id=user_id,
        )
