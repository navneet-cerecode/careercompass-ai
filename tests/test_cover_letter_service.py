from models.job import Job
from models.resume import Resume
from models.skill import Skill
from services.tailoring import FactualCoverLetterComposer, FactualTailoringService


def test_cover_letter_composer_uses_only_verified_evidence():
    resume = Resume(
        name="Avery Candidate",
        email="avery@example.com",
        raw_text="Verified resume",
        skills=[Skill(name="Excel"), Skill(name="Communication")],
        experience=["Built weekly inventory reports in Excel."],
        projects=["Forecasted stock requirements for a regional team."],
    )
    job = Job(
        title="Operations Manager",
        company="Example Ltd",
        location="India",
        description="Manage inventory using Excel and SAP.",
        required_skills=[Skill(name="Excel"), Skill(name="SAP")],
        url="https://example.com/jobs/operations",
    )
    plan = FactualTailoringService().create_plan(resume, job)

    content, evidence = FactualCoverLetterComposer().compose(
        resume=resume,
        job=job,
        plan=plan,
    )

    assert content.company_name == "Example Ltd"
    assert content.job_title == "Operations Manager"
    assert "Excel" in content.evidence_paragraph
    assert "Built weekly inventory reports in Excel." in content.evidence_paragraph
    assert "Forecasted stock requirements" in content.motivation_paragraph
    assert "SAP" not in " ".join(content.model_dump().values())
    assert {item.kind for item in evidence} == {"skill", "experience", "project"}
