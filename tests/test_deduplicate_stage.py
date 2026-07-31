from models.job import Job
from services.job_discovery.pipeline.stages.deduplicate_stage import DeduplicateStage


def make_job(*, title: str, company: str, location: str, url: str) -> Job:
    return Job(
        title=title,
        company=company,
        location=location,
        description="Example description",
        url=url,
    )


def test_deduplicate_stage_keeps_first_matching_company_title_and_location():
    first = make_job(
        title="Data Engineer",
        company="Example Corp",
        location="Bengaluru",
        url="https://example.com/jobs/1",
    )
    duplicate = make_job(
        title="DATA ENGINEER",
        company="EXAMPLE CORP",
        location="BENGALURU",
        url="https://example.com/jobs/2",
    )
    distinct = make_job(
        title="Data Engineer",
        company="Example Corp",
        location="Hyderabad",
        url="https://example.com/jobs/3",
    )

    result = DeduplicateStage().process([first, duplicate, distinct])

    assert result == [first, distinct]
