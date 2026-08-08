from io import BytesIO

from docx import Document
import pdfplumber

from models.skill import Skill
from models.tailored_resume import TailoredResumeContent
from services.tailoring import ResumeDocumentExporter


def sample_content() -> TailoredResumeContent:
    return TailoredResumeContent(
        name="Avery Candidate",
        email="avery@example.com",
        phone="+1 555 0100",
        linkedin="linkedin.com/in/avery",
        skills=(Skill(name="Excel"), Skill(name="Communication")),
        experience=("Built weekly inventory reports in Excel.",),
        projects=("Forecasted stock requirements for a regional team.",),
        education=("Bachelor of Commerce, Example University",),
        certifications=("Supply Chain Fundamentals",),
        achievements=("Recognized for accurate monthly reporting.",),
    )


def test_docx_export_is_readable_and_contains_only_accepted_content():
    payload = ResumeDocumentExporter().render(sample_content(), "docx")

    assert payload.startswith(b"PK")
    document = Document(BytesIO(payload))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert "Avery Candidate" in text
    assert "Built weekly inventory reports in Excel." in text
    assert "Inventory Planning" not in text
    assert document.core_properties.author in (None, "")


def test_pdf_export_is_readable_and_contains_only_accepted_content():
    payload = ResumeDocumentExporter().render(sample_content(), "pdf")

    assert payload.startswith(b"%PDF")
    with pdfplumber.open(BytesIO(payload)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    assert "Avery Candidate" in text
    assert "Built weekly inventory reports in Excel." in text
    assert "Inventory Planning" not in text
