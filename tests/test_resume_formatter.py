from models.resume import Resume
from models.skill import Skill
from services.formatters.resume_formatter import ResumeFormatter


def test_resume_formatter_includes_source_text_and_normalized_skills():
    resume = Resume(
        name="Ada Lovelace",
        raw_text="Ada Lovelace\nBuilt an analytical engine.",
        skills=[Skill(name="python"), Skill(name="sql")],
    )

    formatted = ResumeFormatter().to_text(resume)

    assert "Built an analytical engine." in formatted
    assert "Normalized skills: Python, SQL" in formatted
