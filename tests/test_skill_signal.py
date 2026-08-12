from models.job import Job
from models.resume import Resume
from models.skill import Skill
from services.recommendation.signals.skill_signal import SkillSignal


def make_resume(*skills: str) -> Resume:
    return Resume(
        name="Ada Lovelace",
        raw_text="Reviewed resume",
        skills=[Skill(name=skill) for skill in skills],
    )


def make_job(*skills: str) -> Job:
    return Job(
        title="Role",
        company="Example Corp",
        location="India",
        description="Role description",
        required_skills=[Skill(name=skill) for skill in skills],
        url="https://example.com/jobs/1",
    )


def test_skill_signal_marks_missing_requirements_as_unavailable_evidence():
    component = SkillSignal().evaluate(make_resume("Python"), make_job())

    assert component.evidence_available is False
    assert component.explanation == (
        "This source did not provide structured skill requirements, so skill evidence was not "
        "scored."
    )


def test_skill_signal_uses_curated_aliases_for_nontechnical_skills():
    component = SkillSignal().evaluate(
        make_resume("Customer Relationship Management (CRM)"),
        make_job("CRM"),
    )

    assert component.score == 100
    assert [skill.name for skill in component.matched_skills] == ["CRM"]
