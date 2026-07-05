from models.enums import (
    EmploymentType,
    ExperienceLevel,
    JobSource,
)
from models.job import Job
from models.skill import Skill


job = Job(
    title="Data Scientist",
    company="Google",
    location="Bangalore",
    description="Looking for a Data Scientist with Python and SQL experience.",
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

print(job)