from jobspy import scrape_jobs

print("Searching jobs...")

jobs = scrape_jobs(
    site_name=["linkedin"],
    search_term="Machine Learning Engineer",
    location="India",
    results_wanted=5,
)

print(jobs)

print(f"\nFound {len(jobs)} jobs.")