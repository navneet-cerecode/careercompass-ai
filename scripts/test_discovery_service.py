from services.job_discovery.discovery_service import JobDiscoveryService

service = JobDiscoveryService()

jobs = service.discover(
    role="Data Engineer",
    location="Hyderabad",
)

print("\nJobs Found:\n")

for job in jobs:
    print(job)