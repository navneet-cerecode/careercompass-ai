import pytest
from pydantic import ValidationError

from models.resume import Resume
from models.skill import Skill


def test_resume_model_accepts_a_valid_profile():
    resume = Resume(
        name="Ada Lovelace",
        email="ada@example.com",
        skills=[Skill(name="Python")],
        raw_text="Ada Lovelace\nPython engineer",
    )

    assert resume.name == "Ada Lovelace"
    assert resume.email == "ada@example.com"
    assert resume.skills[0].name == "Python"


def test_resume_model_rejects_invalid_email():
    with pytest.raises(ValidationError):
        Resume(
            name="Ada Lovelace",
            email="not-an-email",
            raw_text="Ada Lovelace",
        )


@pytest.mark.parametrize(
    ("name", "raw_text"),
    [
        ("   ", "Ada Lovelace"),
        ("Ada Lovelace", "   \n"),
    ],
)
def test_resume_model_rejects_blank_identity_or_text(name, raw_text):
    with pytest.raises(ValidationError):
        Resume(name=name, raw_text=raw_text)


def test_resume_collection_defaults_are_isolated():
    first = Resume(name="Ada Lovelace", raw_text="Python engineer")
    second = Resume(name="Grace Hopper", raw_text="Compiler engineer")

    first.experience.append("Analytical Engine")

    assert second.experience == []
