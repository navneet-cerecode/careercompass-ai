"""Stable canonical job fingerprinting."""

import hashlib
import re

from models.job import Job

WHITESPACE = re.compile(r"\s+")


def normalize_fingerprint_text(value: str) -> str:
    return WHITESPACE.sub(" ", value).strip().casefold()


def job_fingerprint(job: Job) -> str:
    """Identify likely duplicate postings independently of provider."""
    identity = "|".join(
        (
            normalize_fingerprint_text(job.company),
            normalize_fingerprint_text(job.title),
            normalize_fingerprint_text(job.location),
        )
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()
