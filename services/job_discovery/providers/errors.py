"""Provider-specific exceptions exposed to discovery orchestration."""


class ProviderError(RuntimeError):
    """Base error for provider configuration, capability, or payload failures."""


class ProviderConfigurationError(ProviderError, ValueError):
    """Provider configuration is missing or invalid."""


class ProviderCapabilityError(ProviderError, NotImplementedError):
    """A requested operation is not supported by the provider."""


class ProviderPayloadError(ProviderError, ValueError):
    """A provider response cannot be normalized safely."""
