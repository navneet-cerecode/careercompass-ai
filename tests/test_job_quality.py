from models.job import Job
import pytest

from services.job_discovery.quality import (
    JobRejectionReason,
    rejection_reason,
    role_matches_title,
)


def make_job(**updates):
    values = {
        "title": "Software Test Engineer",
        "company": "Test Automation Limited",
        "location": "India",
        "description": "Builds reliable automated test systems.",
        "url": "https://example.com/jobs/1",
    }
    values.update(updates)
    return Job(**values)


def test_quality_gate_accepts_legitimate_testing_roles_and_companies():
    assert rejection_reason(make_job()) is None


def test_quality_gate_rejects_synthetic_company_fixtures():
    assert (
        rejection_reason(make_job(company="TestCompany123Blr2023"))
        == JobRejectionReason.SYNTHETIC_LISTING
    )


def test_quality_gate_rejects_placeholder_identity_before_empty_description():
    assert (
        rejection_reason(make_job(company="Unknown", description=""))
        == JobRejectionReason.PLACEHOLDER_IDENTITY
    )


@pytest.mark.parametrize(
    ("role", "title"),
    [
        ("AI Engineer", "Machine Learning Engineer"),
        ("Full Stack Developer", "Python FSD"),
        ("Human Resources Manager", "HR Business Partner"),
        ("Registered Nurse", "Staff Nurse - Emergency Department"),
        ("Customer Service Representative", "Customer Support Agent"),
        ("Sales Manager", "Regional Sales Lead"),
        ("Civil Engineer", "Senior Civil Engineer"),
        ("Chef", "Executive Chef"),
    ],
)
def test_role_matcher_supports_technical_and_nontechnical_careers(role, title):
    assert role_matches_title(role, title) is True


@pytest.mark.parametrize(
    ("role", "title"),
    [
        ("AI Engineer", "Senior Software Engineer"),
        ("AI Engineer", "Senior Business Development Executive"),
        ("Registered Nurse", "Medical Receptionist"),
        ("Sales Manager", "Customer Success Manager"),
        ("Civil Engineer", "Electrical Engineer"),
    ],
)
def test_role_matcher_rejects_titles_from_another_career_lane(role, title):
    assert role_matches_title(role, title) is False


def test_quality_gate_reports_role_mismatch_after_objective_checks():
    assert (
        rejection_reason(make_job(title="Senior Software Engineer"), "AI Engineer")
        == JobRejectionReason.ROLE_MISMATCH
    )
