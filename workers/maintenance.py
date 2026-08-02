"""Reconcile stale tasks, replay the outbox, and purge expired history."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from core.config import Settings
from database.repositories.application_reminders import ApplicationReminderRepository
from database.repositories.task_outbox import TaskOutboxRepository
from database.repositories.tasks import BackgroundTaskRepository
from database.session import Database
from workers.outbox import TaskOutboxDispatcher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TaskMaintenanceResult:
    requeued: int
    cancelled: int
    failed: int
    expired: int
    published: int
    publication_failed: int
    purged: int
    reminders_created: int
    reminders_updated: int
    reminders_dismissed: int


class TaskMaintenance:
    def __init__(
        self,
        *,
        database: Database,
        dispatcher: TaskOutboxDispatcher,
        settings: Settings,
    ) -> None:
        self.database = database
        self.dispatcher = dispatcher
        self.settings = settings

    def run(self, *, now: datetime | None = None) -> TaskMaintenanceResult:
        current = now or datetime.now(timezone.utc)
        with self.database.session() as session:
            tasks = BackgroundTaskRepository(session)
            reconciliation = tasks.reconcile_stale(
                running_before=current - timedelta(seconds=self.settings.task_stale_after_seconds),
                delivery_before=current
                - timedelta(seconds=self.settings.task_delivery_retry_seconds),
                queued_before=current - timedelta(seconds=self.settings.task_queue_expiry_seconds),
                limit=self.settings.task_maintenance_batch_size,
                task_types=("job.discovery",),
            )
            outbox = TaskOutboxRepository(session)
            for task_id in (
                *reconciliation.requeued_task_ids,
                *reconciliation.redelivered_task_ids,
            ):
                outbox.reset(task_id=task_id, actor_name="job_discovery")

        published, publication_failed = self.dispatcher.dispatch_pending(
            limit=self.settings.task_maintenance_batch_size
        )

        with self.database.session() as session:
            purged = BackgroundTaskRepository(session).purge_terminal_before(
                cutoff=current - timedelta(days=self.settings.task_retention_days),
                limit=self.settings.task_maintenance_batch_size,
            )
            reminders = ApplicationReminderRepository(session).reconcile(
                now=current,
                upcoming_before=current
                + timedelta(hours=self.settings.application_reminder_lead_hours),
                limit=self.settings.task_maintenance_batch_size,
            )

        result = TaskMaintenanceResult(
            requeued=(
                len(reconciliation.requeued_task_ids) + len(reconciliation.redelivered_task_ids)
            ),
            cancelled=reconciliation.cancelled_count,
            failed=reconciliation.failed_count,
            expired=reconciliation.expired_count,
            published=published,
            publication_failed=publication_failed,
            purged=purged,
            reminders_created=reminders.created,
            reminders_updated=reminders.updated,
            reminders_dismissed=reminders.dismissed,
        )
        logger.info(
            "Task maintenance completed; requeued=%s cancelled=%s failed=%s "
            "expired=%s published=%s publication_failed=%s purged=%s "
            "reminders_created=%s reminders_updated=%s reminders_dismissed=%s",
            result.requeued,
            result.cancelled,
            result.failed,
            result.expired,
            result.published,
            result.publication_failed,
            result.purged,
            result.reminders_created,
            result.reminders_updated,
            result.reminders_dismissed,
        )
        return result
