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


def test_resume_extractor_reads_non_technical_capabilities_from_skills_section():
    text = """Asha Patel
asha@example.com

Core competencies
Patient assessment, Electronic health records
CPR; Care coordination

Experience
Staff nurse at City Hospital
"""

    resume = ResumeExtractor().extract(text)

    assert {skill.name for skill in resume.skills} == {
        "Patient Assessment",
        "Electronic Health Records",
        "CPR",
        "Care Coordination",
    }
    assert all(skill.category == "Declared capability" for skill in resume.skills)


def test_resume_extractor_preserves_wrapped_section_evidence():
    text = """Avery Candidate
avery@example.com

Education
Bachelor of Commerce, 2026
Example University

Experience
• Regional Retailer, 2025 - 2026
Operations Coordinator
◦ Built weekly inventory reports using Excel and
shared results with five store managers.
◦ Coordinated vendor delivery schedules.

Projects
• Stock Forecast
◦ Forecasted monthly stock requirements using Excel.

Technical Skills and Interests
• Operations: Inventory planning, Vendor management
• Tools: Excel, Power BI

Certifications
• Supply Chain Fundamentals - 2025
"""

    resume = ResumeExtractor().extract(text)

    assert resume.education == ["Bachelor of Commerce, 2026", "Example University"]
    assert resume.experience == [
        "Regional Retailer, 2025 - 2026 Operations Coordinator",
        "Built weekly inventory reports using Excel and shared results with five store managers.",
        "Coordinated vendor delivery schedules.",
    ]
    assert resume.projects == [
        "Stock Forecast",
        "Forecasted monthly stock requirements using Excel.",
    ]
    assert resume.certifications == ["Supply Chain Fundamentals - 2025"]
    assert {skill.name for skill in resume.skills} >= {
        "Inventory Planning",
        "Vendor Management",
        "Excel",
        "Power BI",
    }


def test_resume_extractor_rejoins_wrapped_skill_phrases():
    text = """Avery Candidate
avery@example.com

Technical Skills and Interests
• Coursework: Computer Networks, Cloud
Computing, DBMS
• Development: WebRTC, REST APIs

Certifications
• Career Foundations - 2026
"""

    resume = ResumeExtractor().extract(text)
    names = {skill.name for skill in resume.skills}

    assert names >= {"Computer Networks", "Cloud Computing", "DBMS", "WebRTC", "REST APIs"}
    assert "Cloud" not in names
    assert "Computing" not in names
