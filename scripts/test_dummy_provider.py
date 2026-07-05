from services.job_discovery.providers.dummy_provider import DummyProvider

provider = DummyProvider()

jobs = provider.search(
    role="Deep Learning Engineer",
    location="Pune"
)

print(jobs)