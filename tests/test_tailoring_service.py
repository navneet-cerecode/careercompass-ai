from models.job import Job
from models.resume import Resume
from models.skill import Skill
from services.tailoring import FactualTailoringService


def test_factual_tailoring_prioritizes_without_adding_resume_claims():
    resume = Resume(
        name="Asha Patel",
        raw_text="Operations coordinator with Excel and vendor management experience.",
        skills=[Skill(name="Communication"), Skill(name="Excel")],
        experience=[
            "Coordinated weekly team meetings.",
            "Built Excel inventory reports for regional operations.",
        ],
        projects=[
            "Created a volunteer scheduling guide.",
            "Reduced inventory reconciliation delays using Excel.",
        ],
    )
    job = Job(
        title="Operations Manager",
        company="Example Ltd",
        location="India",
        description="Manage inventory operations using Excel.",
        required_skills=[Skill(name="Excel"), Skill(name="Inventory Planning")],
        url="https://example.com/jobs/operations-manager",
    )

    plan = FactualTailoringService().create_plan(resume, job)

    assert [skill.name for skill in plan.skills] == ["Excel", "Communication"]
    assert [skill.name for skill in plan.matched_skills] == ["Excel"]
    assert [skill.name for skill in plan.missing_skills] == ["Inventory Planning"]
    assert plan.experience[0] == resume.experience[1]
    assert plan.projects[0] == resume.projects[1]
    assert sorted(plan.experience) == sorted(resume.experience)
    assert sorted(plan.projects) == sorted(resume.projects)
    assert {skill.name for skill in plan.skills} == {skill.name for skill in resume.skills}
    assert plan.user_review_required is True
    assert plan.algorithm_version == "factual-ordering-v1"


def test_factual_tailoring_preserves_original_order_when_nothing_matches():
    resume = Resume(
        name="Asha Patel",
        raw_text="Customer support specialist.",
        skills=[Skill(name="Customer Service")],
        experience=["Resolved customer enquiries.", "Maintained support records."],
        projects=["Organized a community event."],
    )
    job = Job(
        title="Payroll Analyst",
        company="Example Ltd",
        location="India",
        description="Process monthly payroll.",
        required_skills=[Skill(name="Payroll")],
        url="https://example.com/jobs/payroll-analyst",
    )

    plan = FactualTailoringService().create_plan(resume, job)

    assert plan.experience == tuple(resume.experience)
    assert plan.projects == tuple(resume.projects)
    assert plan.evidence == ()
    assert [skill.name for skill in plan.missing_skills] == ["Payroll"]
