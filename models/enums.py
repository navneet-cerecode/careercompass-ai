"""
File: models/enums.py

Description:
Contains shared enumerations used across the domain models.

Author:
Navneet Prakash Yadav
"""

from enum import Enum


class ExperienceLevel(str, Enum):
    """Supported job experience levels."""

    ENTRY = "Entry"
    MID = "Mid"
    SENIOR = "Senior"
    LEAD = "Lead"
    PRINCIPAL = "Principal"


class EmploymentType(str, Enum):
    """Supported employment types."""

    FULL_TIME = "Full Time"
    PART_TIME = "Part Time"
    INTERNSHIP = "Internship"
    CONTRACT = "Contract"
    REMOTE = "Remote"


class JobSource(str, Enum):
    """Supported job providers."""

    JSEARCH = "JSearch"
    ADZUNA = "Adzuna"
    ARBEITNOW = "Arbeitnow"
    THE_MUSE = "The Muse"
    WORKDAY = "Workday"
    GREENHOUSE = "Greenhouse"
    SMARTRECRUITERS = "SmartRecruiters"
    ASHBY = "Ashby"
    LEVER = "Lever"
    COMPANY = "Company"
    OTHER = "Other"


class ApplicationStatus(str, Enum):
    """User-visible stages in the assisted application workflow."""

    DISCOVERED = "Discovered"
    SAVED = "Saved"
    PREPARING = "Preparing"
    READY_TO_APPLY = "Ready to apply"
    APPLIED = "Applied"
    UNDER_REVIEW = "Under review"
    ASSESSMENT = "Assessment"
    INTERVIEW = "Interview"
    OFFER = "Offer"
    REJECTED = "Rejected"
    WITHDRAWN = "Withdrawn"


class BackgroundTaskStatus(str, Enum):
    """Durable lifecycle states for background work."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
