from models.enums import (
    EmploymentType,
    ExperienceLevel,
    JobSource,
)
from models.job import Job
from models.match import MatchResult
from models.skill import Skill

job = Job(
    title="Data Scientist",
    company="Google",
    location="Bangalore",
    description="Python, SQL and Machine Learning required.",
    required_skills=[
        Skill(name="Python"),
        Skill(name="SQL"),
        Skill(name="Machine Learning"),
    ],
    experience_level=ExperienceLevel.ENTRY,
    employment_type=EmploymentType.FULL_TIME,
    source=JobSource.GREENHOUSE,
    url="https://careers.google.com/",
)

result = MatchResult(
    job=job,
    match_score=86.5,
    matched_skills=[
        Skill(name="Python"),
        Skill(name="SQL"),
    ],
    missing_skills=[
        Skill(name="Machine Learning"),
    ],
    recruiter_summary=(
        "The candidate demonstrates strong Python and SQL skills but "
        "would benefit from additional machine learning experience."
    ),
    recommendations=[
        "Build one end-to-end Machine Learning project.",
        "Highlight SQL projects in the resume.",
    ],
)

print(result)