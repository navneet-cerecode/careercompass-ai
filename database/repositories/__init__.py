"""Persistence repository implementations."""

from database.repositories.applications import (
    ApplicationRepository,
    InvalidApplicationTransition,
    SavedJobRepository,
)
from database.repositories.application_reminders import ApplicationReminderRepository
from database.repositories.application_packets import ApplicationPacketRepository
from database.repositories.jobs import JobRepository
from database.repositories.history import (
    RecommendationHistoryRepository,
    SearchHistory,
    SearchHistoryRepository,
)
from database.repositories.resumes import PersistedResume, ResumeRepository
from database.repositories.tasks import (
    BackgroundTaskRepository,
    IdempotencyConflict,
    InvalidTaskTransition,
)
from database.repositories.subscriptions import SubscriptionRepository
from database.repositories.tailoring import PersistedTailoringPlan, TailoringPlanRepository
from database.repositories.tailored_resumes import TailoredResumeRepository
from database.repositories.cover_letters import CoverLetterRepository
from database.repositories.users import User, UserRepository

__all__ = [
    "ApplicationRepository",
    "ApplicationReminderRepository",
    "ApplicationPacketRepository",
    "BackgroundTaskRepository",
    "CoverLetterRepository",
    "IdempotencyConflict",
    "InvalidApplicationTransition",
    "InvalidTaskTransition",
    "JobRepository",
    "RecommendationHistoryRepository",
    "PersistedResume",
    "PersistedTailoringPlan",
    "ResumeRepository",
    "SearchHistory",
    "SearchHistoryRepository",
    "SavedJobRepository",
    "SubscriptionRepository",
    "TailoringPlanRepository",
    "TailoredResumeRepository",
    "User",
    "UserRepository",
]
