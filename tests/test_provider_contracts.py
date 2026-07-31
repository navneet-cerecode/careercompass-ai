import pytest
from pydantic import ValidationError

from services.job_discovery.providers.base_provider import BaseProvider
from services.job_discovery.providers.contracts import (
    DatePosted,
    JobSearchQuery,
    ProviderHealthStatus,
)
from services.job_discovery.providers.dummy_provider import DummyProvider
from services.job_discovery.providers.errors import ProviderCapabilityError
from services.jobs.providers.base_provider import BaseProvider as LegacyBaseProvider


def test_duplicate_base_provider_import_resolves_to_canonical_contract():
    assert LegacyBaseProvider is BaseProvider


def test_search_query_normalizes_text_and_country():
    query = JobSearchQuery(
        role="  Data Engineer  ",
        location="  Bengaluru  ",
        country="IN",
        date_posted=DatePosted.WEEK,
    )

    assert query.role == "Data Engineer"
    assert query.location == "Bengaluru"
    assert query.country == "in"
    assert query.date_posted == DatePosted.WEEK


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("role", "   "),
        ("location", "   "),
        ("page", 0),
        ("page_size", 101),
    ],
)
def test_search_query_rejects_invalid_values(field, value):
    data = {
        "role": "Data Engineer",
        "location": "India",
        field: value,
    }

    with pytest.raises(ValidationError):
        JobSearchQuery(**data)


def test_legacy_search_method_adapts_to_typed_query():
    provider = DummyProvider()

    jobs = provider.search("Data Engineer", "India")

    assert len(jobs) == 1
    assert jobs[0].title == "Data Engineer"
    assert jobs[0].location == "India"
    assert provider.name == "dummy"
    assert provider.capabilities.location_filter is True


def test_default_health_and_detail_behavior_is_explicit():
    provider = DummyProvider()

    health = provider.health_check()

    assert health.provider_name == "dummy"
    assert health.status == ProviderHealthStatus.UNKNOWN
    assert provider.capabilities.live_health_check is False

    with pytest.raises(ProviderCapabilityError):
        provider.get_job_details("external-id")
