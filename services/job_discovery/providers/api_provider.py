"""Backward-compatible import for the named JSearch provider."""

from services.job_discovery.providers.jsearch_provider import JSearchProvider

APIProvider = JSearchProvider

__all__ = ["APIProvider"]
