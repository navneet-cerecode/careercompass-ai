"""Idempotent durable lifecycle repository for background work."""

import hashlib
import re
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.models.tasks import BackgroundTaskRecord
from database.models.users import UserRecord
from models.background_task import BackgroundTask
from models.enums import BackgroundTaskStatus

TASK_TYPE_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]{0,99}$")
ERROR_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,99}$")


class IdempotencyConflict(ValueError):
    """Raised when a key is reused for different task inputs."""


class InvalidTaskTransition(ValueError):
    """Raised when a task lifecycle operation is not allowed."""


class BackgroundTaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        task_type: str,
        idempotency_key: str,
        user_id: UUID | None = None,
        resource_id: UUID | None = None,
        max_attempts: int = 4,
    ) -> BackgroundTask:
        normalized_type = self._normalize_task_type(task_type)
        normalized_key = idempotency_key.strip()
        if not 8 <= len(normalized_key) <= 200:
            raise ValueError("Idempotency keys must contain between 8 and 200 characters.")
        if not 1 <= max_attempts <= 11:
            raise ValueError("max_attempts must be between 1 and 11.")
        if user_id is not None and self.session.get(UserRecord, user_id) is None:
            raise ValueError("User does not exist.")

        fingerprint = self._fingerprint(
            task_type=normalized_type,
            idempotency_key=normalized_key,
            user_id=user_id,
        )
        existing = self._get_by_fingerprint(fingerprint)
        if existing is not None:
            return self._resolve_idempotent_create(
                existing,
                resource_id=resource_id,
                max_attempts=max_attempts,
            )

        record = BackgroundTaskRecord(
            user_id=user_id,
            task_type=normalized_type,
            status=BackgroundTaskStatus.QUEUED.value,
            resource_id=resource_id,
            idempotency_fingerprint=fingerprint,
            attempt_count=0,
            max_attempts=max_attempts,
        )
        try:
            with self.session.begin_nested():
                self.session.add(record)
                self.session.flush()
        except IntegrityError:
            existing = self._get_by_fingerprint(fingerprint)
            if existing is None:
                raise
            return self._resolve_idempotent_create(
                existing,
                resource_id=resource_id,
                max_attempts=max_attempts,
            )

        self.session.refresh(record)
        return self._to_domain(record)

    def get(
        self,
        *,
        task_id: UUID,
        user_id: UUID | None,
    ) -> BackgroundTask | None:
        record = self._get_owned_record(task_id=task_id, user_id=user_id)
        return self._to_domain(record) if record is not None else None

    def list(self, *, user_id: UUID) -> tuple[BackgroundTask, ...]:
        records = self.session.scalars(
            select(BackgroundTaskRecord)
            .where(BackgroundTaskRecord.user_id == user_id)
            .order_by(
                BackgroundTaskRecord.created_at.desc(),
                BackgroundTaskRecord.id,
            )
        ).all()
        return tuple(self._to_domain(record) for record in records)

    def start(
        self,
        *,
        task_id: UUID,
        user_id: UUID | None,
    ) -> BackgroundTask | None:
        record = self._get_owned_record(
            task_id=task_id,
            user_id=user_id,
            for_update=True,
        )
        if record is None:
            return None
        self._require_status(record, BackgroundTaskStatus.QUEUED)

        now = datetime.now(timezone.utc)
        record.status = BackgroundTaskStatus.RUNNING.value
        record.attempt_count += 1
        record.error_code = None
        record.started_at = now
        record.updated_at = now
        record.finished_at = None
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    def complete(
        self,
        *,
        task_id: UUID,
        user_id: UUID | None,
    ) -> BackgroundTask | None:
        record = self._get_owned_record(
            task_id=task_id,
            user_id=user_id,
            for_update=True,
        )
        if record is None:
            return None
        self._require_status(record, BackgroundTaskStatus.RUNNING)

        now = datetime.now(timezone.utc)
        record.status = BackgroundTaskStatus.SUCCEEDED.value
        record.error_code = None
        record.updated_at = now
        record.finished_at = now
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    def record_failure(
        self,
        *,
        task_id: UUID,
        user_id: UUID | None,
        error_code: str,
        retryable: bool,
    ) -> BackgroundTask | None:
        normalized_error = self._normalize_error_code(error_code)
        record = self._get_owned_record(
            task_id=task_id,
            user_id=user_id,
            for_update=True,
        )
        if record is None:
            return None
        self._require_status(record, BackgroundTaskStatus.RUNNING)

        now = datetime.now(timezone.utc)
        can_retry = retryable and record.attempt_count < record.max_attempts
        record.status = (
            BackgroundTaskStatus.QUEUED.value if can_retry else BackgroundTaskStatus.FAILED.value
        )
        record.error_code = normalized_error
        record.updated_at = now
        record.started_at = None if can_retry else record.started_at
        record.finished_at = None if can_retry else now
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    def cancel(
        self,
        *,
        task_id: UUID,
        user_id: UUID | None,
    ) -> BackgroundTask | None:
        record = self._get_owned_record(
            task_id=task_id,
            user_id=user_id,
            for_update=True,
        )
        if record is None:
            return None
        self._require_status(record, BackgroundTaskStatus.QUEUED)

        now = datetime.now(timezone.utc)
        record.status = BackgroundTaskStatus.CANCELLED.value
        record.error_code = None
        record.updated_at = now
        record.finished_at = now
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    def _get_owned_record(
        self,
        *,
        task_id: UUID,
        user_id: UUID | None,
        for_update: bool = False,
    ) -> BackgroundTaskRecord | None:
        statement = select(BackgroundTaskRecord).where(
            BackgroundTaskRecord.id == task_id,
            BackgroundTaskRecord.user_id == user_id
            if user_id is not None
            else BackgroundTaskRecord.user_id.is_(None),
        )
        if for_update:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def _get_by_fingerprint(self, fingerprint: str) -> BackgroundTaskRecord | None:
        return self.session.scalar(
            select(BackgroundTaskRecord).where(
                BackgroundTaskRecord.idempotency_fingerprint == fingerprint
            )
        )

    def _resolve_idempotent_create(
        self,
        record: BackgroundTaskRecord,
        *,
        resource_id: UUID | None,
        max_attempts: int,
    ) -> BackgroundTask:
        if record.resource_id != resource_id or record.max_attempts != max_attempts:
            raise IdempotencyConflict("Idempotency key was already used for different task inputs.")
        return self._to_domain(record)

    @staticmethod
    def _fingerprint(
        *,
        task_type: str,
        idempotency_key: str,
        user_id: UUID | None,
    ) -> str:
        owner_scope = str(user_id) if user_id is not None else "anonymous"
        material = f"{owner_scope}\0{task_type}\0{idempotency_key}".encode()
        return hashlib.sha256(material).hexdigest()

    @staticmethod
    def _normalize_task_type(task_type: str) -> str:
        normalized = task_type.strip().casefold()
        if TASK_TYPE_PATTERN.fullmatch(normalized) is None:
            raise ValueError(
                "Task types must use lowercase letters, numbers, dots, dashes, or underscores."
            )
        return normalized

    @staticmethod
    def _normalize_error_code(error_code: str) -> str:
        normalized = error_code.strip().casefold()
        if ERROR_CODE_PATTERN.fullmatch(normalized) is None:
            raise ValueError("Error codes must use lowercase letters, numbers, or underscores.")
        return normalized

    @staticmethod
    def _require_status(
        record: BackgroundTaskRecord,
        expected: BackgroundTaskStatus,
    ) -> None:
        current = BackgroundTaskStatus(record.status)
        if current != expected:
            raise InvalidTaskTransition(
                f"Task must be {expected.value!r}; current status is {current.value!r}."
            )

    @staticmethod
    def _to_domain(record: BackgroundTaskRecord) -> BackgroundTask:
        return BackgroundTask.model_validate(record, from_attributes=True)
