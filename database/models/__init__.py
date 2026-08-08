"""SQLAlchemy persistence models."""

from database.models.applications import (
    ApplicationEventRecord,
    ApplicationPacketRecord,
    ApplicationReminderRecord,
    ApplicationRecord,
    SavedJobRecord,
)
from database.models.jobs import JobRecord, JobSourceRecord
from database.models.identities import UserIdentityRecord
from database.models.job_discovery_tasks import (
    JobDiscoveryTaskRecord,
    JobDiscoveryTaskResultRecord,
)
from database.models.recommendations import (
    RecommendationRecord,
    SearchRecord,
    SearchResultRecord,
)
from database.models.resumes import ResumeRecord, ResumeSkillRecord, SkillRecord
from database.models.tasks import BackgroundTaskRecord, TaskOutboxRecord
from database.models.subscriptions import SubscriptionRecord
from database.models.tailoring import CoverLetterRecord, TailoredResumeRecord, TailoringPlanRecord
from database.models.users import UserRecord

__all__ = [
    "ApplicationEventRecord",
    "ApplicationPacketRecord",
    "ApplicationReminderRecord",
    "ApplicationRecord",
    "BackgroundTaskRecord",
    "CoverLetterRecord",
    "JobRecord",
    "JobDiscoveryTaskRecord",
    "JobDiscoveryTaskResultRecord",
    "JobSourceRecord",
    "RecommendationRecord",
    "ResumeRecord",
    "ResumeSkillRecord",
    "SearchRecord",
    "SearchResultRecord",
    "SavedJobRecord",
    "SkillRecord",
    "SubscriptionRecord",
    "TailoringPlanRecord",
    "TailoredResumeRecord",
    "TaskOutboxRecord",
    "UserRecord",
    "UserIdentityRecord",
]
