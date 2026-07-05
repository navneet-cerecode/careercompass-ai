"""
Provider Factory.

Creates provider instances from
company configurations.
"""

from .workday_provider import WorkdayProvider
from services.job_discovery.providers.api_provider import (
    APIProvider,
)



class ProviderFactory:
    """
    Creates providers based on platform.
    """

    PROVIDERS = {

        "workday": WorkdayProvider,

        "api": APIProvider,

    }

    @classmethod
    def create(
        cls,
        company: dict,
    ):

        platform = company["platform"]

        provider_class = cls.PROVIDERS.get(
            platform
        )

        if provider_class is None:

            raise ValueError(
                f"Unsupported platform: {platform}"
            )

        return provider_class(
            company
        )