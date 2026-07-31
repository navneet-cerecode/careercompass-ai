"""Create provider instances from registry configuration."""

from services.job_discovery.providers.base_provider import BaseProvider
from services.job_discovery.providers.contracts import ProviderConfig
from services.job_discovery.providers.errors import ProviderConfigurationError
from services.job_discovery.providers.jsearch_provider import JSearchProvider
from services.job_discovery.providers.workday_provider import WorkdayProvider


class ProviderFactory:
    """Create canonical providers based on platform."""

    PROVIDERS = {
        "workday": WorkdayProvider,
        "jsearch": JSearchProvider,
        "api": JSearchProvider,
    }

    @classmethod
    def create(
        cls,
        company: ProviderConfig,
    ) -> BaseProvider:
        platform = company["platform"]
        provider_class = cls.PROVIDERS.get(platform)

        if provider_class is None:
            raise ProviderConfigurationError(f"Unsupported platform: {platform}")

        return provider_class(company)
