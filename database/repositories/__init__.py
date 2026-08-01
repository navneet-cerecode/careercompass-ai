"""Persistence repository implementations."""

from database.repositories.applications import (
    ApplicationRepository,
    InvalidApplicationTransition,
    SavedJobRepository,
)
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
from database.repositories.users import User, UserRepository

__all__ = [
    "ApplicationRepository",
    "BackgroundTaskRepository",
    "IdempotencyConflict",
    "InvalidApplicationTransition",
    "InvalidTaskTransition",
    "JobRepository",
    "RecommendationHistoryRepository",
    "PersistedResume",
    "ResumeRepository",
    "SearchHistory",
    "SearchHistoryRepository",
    "SavedJobRepository",
    "User",
    "UserRepository",
]
