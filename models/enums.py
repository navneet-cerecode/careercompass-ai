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

    GREENHOUSE = "Greenhouse"

    LEVER = "Lever"

    COMPANY = "Company"

    OTHER = "Other"