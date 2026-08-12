"""Objective quality checks for normalized provider jobs."""

import re
from enum import StrEnum

from models.job import Job


class JobRejectionReason(StrEnum):
    """Privacy-safe reasons a normalized job cannot enter the catalog."""

    PLACEHOLDER_IDENTITY = "placeholder_identity"
    EMPTY_DESCRIPTION = "empty_description"
    SYNTHETIC_LISTING = "synthetic_listing"
    ROLE_MISMATCH = "role_mismatch"


_PLACEHOLDERS = {"", "n/a", "na", "none", "null", "unknown"}
_SYNTHETIC_COMPANY = re.compile(r"^(?:test|dummy|sample)\s*company(?:\W|\d|$)", re.IGNORECASE)
_ROLE_MODIFIERS = {
    "associate",
    "consultant",
    "coordinator",
    "developer",
    "director",
    "engineer",
    "executive",
    "head",
    "intern",
    "junior",
    "lead",
    "manager",
    "officer",
    "principal",
    "representative",
    "senior",
    "specialist",
    "staff",
    "technician",
}
_ROLE_ALIASES = (
    ("ai", "artificial intelligence", "machine learning", "ml", "genai", "generative ai"),
    ("full stack", "fullstack", "full-stack", "fsd"),
    ("human resources", "hr"),
    ("quality assurance", "qa"),
    ("customer service", "customer support"),
    ("registered nurse", "staff nurse", "nurse"),
    ("user experience", "ux"),
    ("user interface", "ui"),
)


def rejection_reason(job: Job, role: str | None = None) -> JobRejectionReason | None:
    """Return an objective rejection reason, leaving relevance to ranking."""
    identity = (job.title, job.company, job.location)
    if any(value.strip().casefold() in _PLACEHOLDERS for value in identity):
        return JobRejectionReason.PLACEHOLDER_IDENTITY
    if not job.description.strip():
        return JobRejectionReason.EMPTY_DESCRIPTION
    if _SYNTHETIC_COMPANY.match(job.company.strip()):
        return JobRejectionReason.SYNTHETIC_LISTING
    if role and not role_matches_title(role, job.title):
        return JobRejectionReason.ROLE_MISMATCH
    return None


def role_matches_title(role: str, title: str) -> bool:
    """Require every meaningful role concept to appear in the published title."""
    role_text = _normalize_role_text(role)
    title_text = _normalize_role_text(title)
    remaining_terms = set(_role_terms(role_text))
    requirements: list[tuple[str, ...]] = []

    for aliases in _ROLE_ALIASES:
        matched_alias = next((alias for alias in aliases if _contains(role_text, alias)), None)
        if matched_alias is None:
            continue
        requirements.append(aliases)
        remaining_terms.difference_update(_role_terms(matched_alias))

    meaningful_terms = remaining_terms - _ROLE_MODIFIERS
    if not requirements and not meaningful_terms:
        meaningful_terms = remaining_terms

    return all(
        any(_contains(title_text, alias) for alias in aliases) for aliases in requirements
    ) and all(term in _role_terms(title_text) for term in meaningful_terms)


def _normalize_role_text(value: str) -> str:
    return " ".join(re.findall(r"[\w+#.]+", value.casefold()))


def _role_terms(value: str) -> tuple[str, ...]:
    return tuple(value.split())


def _contains(text: str, phrase: str) -> bool:
    normalized_phrase = _normalize_role_text(phrase)
    return f" {normalized_phrase} " in f" {text} "
