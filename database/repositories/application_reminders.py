"""Durable, owner-scoped reminders derived from application plans."""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.models.applications import ApplicationRecord, ApplicationReminderRecord
from models.application import ApplicationReminder
from models.enums import ApplicationReminderStatus, ApplicationStatus

TERMINAL_APPLICATION_STATUSES = (
    ApplicationStatus.REJECTED.value,
    ApplicationStatus.WITHDRAWN.value,
)


@dataclass(frozen=True)
class ReminderReconciliation:
    created: int = 0
    updated: int = 0
    dismissed: int = 0


class ApplicationReminderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def reconcile(
        self,
        *,
        now: datetime,
        upcoming_before: datetime,
        limit: int,
    ) -> ReminderReconciliation:
        created = 0
        updated = 0
        dismissed = 0

        active = self.session.scalars(
            select(ApplicationReminderRecord)
            .where(ApplicationReminderRecord.status != ApplicationReminderStatus.DISMISSED.value)
            .limit(limit)
        ).all()
        for reminder in active:
            application = self.session.get(ApplicationRecord, reminder.application_id)
            is_stale = (
                application is None
                or application.status in TERMINAL_APPLICATION_STATUSES
                or application.next_action_due_at is None
                or application.next_action_due_at != reminder.due_at
                or not application.next_action
            )
            if is_stale:
                reminder.status = ApplicationReminderStatus.DISMISSED.value
                reminder.dismissed_at = now
                reminder.updated_at = now
                dismissed += 1

        eligible = self.session.scalars(
            select(ApplicationRecord)
            .where(
                ApplicationRecord.next_action_due_at.is_not(None),
                ApplicationRecord.next_action_due_at <= upcoming_before,
                ApplicationRecord.next_action.is_not(None),
                ApplicationRecord.next_action != "",
                ApplicationRecord.status.not_in(TERMINAL_APPLICATION_STATUSES),
            )
            .order_by(ApplicationRecord.next_action_due_at, ApplicationRecord.id)
            .limit(limit)
        ).all()
        for application in eligible:
            reminder = self.session.scalar(
                select(ApplicationReminderRecord).where(
                    ApplicationReminderRecord.application_id == application.id,
                    ApplicationReminderRecord.due_at == application.next_action_due_at,
                )
            )
            if reminder is None:
                try:
                    with self.session.begin_nested():
                        self.session.add(
                            ApplicationReminderRecord(
                                user_id=application.user_id,
                                application_id=application.id,
                                due_at=application.next_action_due_at,
                                next_action=application.next_action,
                                status=ApplicationReminderStatus.UNREAD.value,
                            )
                        )
                        self.session.flush()
                except IntegrityError:
                    # Another maintenance runner created the same deadline reminder.
                    pass
                else:
                    created += 1
            elif (
                reminder.status != ApplicationReminderStatus.DISMISSED.value
                and reminder.next_action != application.next_action
            ):
                reminder.next_action = application.next_action
                reminder.updated_at = now
                updated += 1

        self.session.flush()
        return ReminderReconciliation(
            created=created,
            updated=updated,
            dismissed=dismissed,
        )

    def list(self, *, user_id: UUID) -> tuple[ApplicationReminder, ...]:
        records = self.session.scalars(
            select(ApplicationReminderRecord)
            .where(
                ApplicationReminderRecord.user_id == user_id,
                ApplicationReminderRecord.status != ApplicationReminderStatus.DISMISSED.value,
            )
            .order_by(
                ApplicationReminderRecord.due_at,
                ApplicationReminderRecord.created_at,
            )
        ).all()
        return tuple(self._to_domain(record) for record in records)

    def set_status(
        self,
        *,
        user_id: UUID,
        reminder_id: UUID,
        status: ApplicationReminderStatus,
    ) -> ApplicationReminder | None:
        record = self.session.scalar(
            select(ApplicationReminderRecord).where(
                ApplicationReminderRecord.id == reminder_id,
                ApplicationReminderRecord.user_id == user_id,
            )
        )
        if record is None:
            return None
        current = datetime.now(timezone.utc)
        record.status = status.value
        record.read_at = current if status == ApplicationReminderStatus.READ else None
        record.dismissed_at = current if status == ApplicationReminderStatus.DISMISSED else None
        record.updated_at = current
        self.session.flush()
        self.session.refresh(record)
        return self._to_domain(record)

    @staticmethod
    def _to_domain(record: ApplicationReminderRecord) -> ApplicationReminder:
        return ApplicationReminder.model_validate(record, from_attributes=True)
