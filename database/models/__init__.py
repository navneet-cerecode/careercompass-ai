"""SQLAlchemy persistence models."""

from database.models.applications import (
    ApplicationEventRecord,
    ApplicationRecord,
    SavedJobRecord,
)
from database.models.jobs import JobRecord, JobSourceRecord
from database.models.recommendations import (
    RecommendationRecord,
    SearchRecord,
    SearchResultRecord,
)
from database.models.resumes import ResumeRecord, ResumeSkillRecord, SkillRecord
from database.models.tasks import BackgroundTaskRecord
from database.models.users import UserRecord

__all__ = [
    "ApplicationEventRecord",
    "ApplicationRecord",
    "BackgroundTaskRecord",
    "JobRecord",
    "JobSourceRecord",
    "RecommendationRecord",
    "ResumeRecord",
    "ResumeSkillRecord",
    "SearchRecord",
    "SearchResultRecord",
    "SavedJobRecord",
    "SkillRecord",
    "UserRecord",
]
