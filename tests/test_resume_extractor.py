from services.resume.extractor import ResumeExtractor


def test_resume_extractor_returns_contact_details_and_known_skills():
    text = """Ada Lovelace
ada@example.com
+91 98765 43210
linkedin.com/in/ada-lovelace
github.com/ada-lovelace

Built Python and SQL data systems using Docker.
"""

    resume = ResumeExtractor().extract(text)

    assert resume.name == "Ada Lovelace"
    assert resume.email == "ada@example.com"
    assert resume.linkedin == "https://linkedin.com/in/ada-lovelace"
    assert resume.github == "https://github.com/ada-lovelace"
    assert {skill.name.lower() for skill in resume.skills} >= {"python", "sql", "docker"}
    assert resume.raw_text == text
