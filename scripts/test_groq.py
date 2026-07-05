from models.enums import (
    EmploymentType,
    ExperienceLevel,
    JobSource,
)

from models.job import Job
from models.skill import Skill

from services.resume.parser_service import ResumeParserService
from services.resume.extractor import ResumeExtractor

from services.llm.evaluator import ResumeEvaluator


parser = ResumeParserService()

extractor = ResumeExtractor()

path = input("Resume path: ")

text = parser.parse(path)

resume = extractor.extract(text)

job = Job(

    title="Machine Learning Engineer",

    company="NVIDIA",

    location="India",

    description="""
Looking for Python, PyTorch,
Docker, SQL,
Machine Learning,
Deep Learning.
""",

    required_skills=[
        Skill(name="Python"),
        Skill(name="PyTorch"),
        Skill(name="Docker"),
        Skill(name="SQL"),
        Skill(name="Machine Learning"),
    ],

    experience_level=ExperienceLevel.ENTRY,

    employment_type=EmploymentType.FULL_TIME,

    source=JobSource.OTHER,

    url="https://example.com",
)

evaluator = ResumeEvaluator()

result = evaluator.evaluate(
    resume,
    job,
)

print()

print("=" * 60)

print(result)

print("=" * 60)