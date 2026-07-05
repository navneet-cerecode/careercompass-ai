"""
Test the Recommendation Engine.
"""

from models.enums import (
    EmploymentType,
    ExperienceLevel,
    JobSource,
)
from models.job import Job
from models.skill import Skill

from services.resume.extractor import ResumeExtractor
from services.resume.parser_service import ResumeParserService

from services.recommendation.recommendation_engine import (
    RecommendationEngine,
)


# ---------------------------------------------------------
# Load Resume
# ---------------------------------------------------------

resume_path = input(
    "Resume Path: "
).strip().strip('"')

parser = ResumeParserService()

extractor = ResumeExtractor()

text = parser.parse(
    resume_path
)

resume = extractor.extract(
    text
)

# ---------------------------------------------------------
# Dummy Job
# ---------------------------------------------------------

job = Job(

    title="Machine Learning Engineer",

    company="NVIDIA",

    location="India",

    description="""
Looking for Python,
PyTorch,
Docker,
SQL,
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

# ---------------------------------------------------------
# Recommendation Engine
# ---------------------------------------------------------

engine = RecommendationEngine()

result = engine.evaluate(
    resume,
    job,
)

# ---------------------------------------------------------
# Print
# ---------------------------------------------------------

print("\n")

print("=" * 60)

print("FINAL SCORE")

print(result.score)

print("\nSIGNALS\n")

for signal in result.signal_results:

    print(signal.signal_name)

    print(signal.score)

    print(signal.reason)

    print()

    print("Matched Skills")

    for skill in signal.matched_skills:

        print("-", skill.name)

    print()

    print("Missing Skills")

    for skill in signal.missing_skills:

        print("-", skill.name)

    print()

print("=" * 60)