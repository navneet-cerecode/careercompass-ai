from services.job_discovery.providers.companies import COMPANIES

print("Supported Companies:\n")

for company in COMPANIES:
    print(company["name"])
    print("Platform:", company["platform"])

    if careers_url := company.get("careers_url"):
        print(careers_url)

    print()
