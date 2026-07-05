from services.job_discovery.providers.companies import COMPANIES

print("Supported Companies:\n")

for company in COMPANIES:
    print(company["name"])
    print(company["careers_url"])
    print()