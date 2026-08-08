import pytest
from pydantic import ValidationError

from models.skill import Skill


def test_skill_model_trims_and_normalizes_name():
    skill = Skill(name=" python ")

    assert skill.name == "Python"


def test_skill_model_rejects_blank_name():
    with pytest.raises(ValidationError):
        Skill(name="   ")


@pytest.mark.parametrize(
    ("raw_name", "canonical_name"),
    [
        ("sql", "SQL"),
        ("PYTORCH", "PyTorch"),
        ("javascript", "JavaScript"),
        ("c++", "C++"),
    ],
)
def test_skill_model_preserves_canonical_technology_names(raw_name, canonical_name):
    assert Skill(name=raw_name).name == canonical_name


@pytest.mark.parametrize("name", ["CPR", "RN", "CPA"])
def test_skill_model_preserves_occupational_acronyms(name):
    assert Skill(name=name).name == name
