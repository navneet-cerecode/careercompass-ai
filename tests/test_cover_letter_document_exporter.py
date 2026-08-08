from io import BytesIO

from docx import Document
import pdfplumber

from models.cover_letter import CoverLetterContent
from services.tailoring import CoverLetterDocumentExporter


def sample_content() -> CoverLetterContent:
    return CoverLetterContent(
        candidate_name="Avery Candidate",
        candidate_email="avery@example.com",
        company_name="Example Ltd",
        job_title="Operations Manager",
        salutation="Dear hiring team,",
        opening="I am applying for the Operations Manager position at Example Ltd.",
        evidence_paragraph="My verified background includes Excel.",
        motivation_paragraph="A related project from my resume is: Stock forecast.",
        closing_paragraph="Thank you for considering my application.",
        sign_off="Sincerely,",
    )


def test_cover_letter_docx_is_private_and_readable():
    payload = CoverLetterDocumentExporter().render(sample_content(), "docx")

    assert payload.startswith(b"PK")
    document = Document(BytesIO(payload))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert "Operations Manager at Example Ltd" in text
    assert "My verified background includes Excel." in text
    assert document.core_properties.author in (None, "")


def test_cover_letter_pdf_is_readable():
    payload = CoverLetterDocumentExporter().render(sample_content(), "pdf")

    assert payload.startswith(b"%PDF")
    with pdfplumber.open(BytesIO(payload)) as pdf:
        assert len(pdf.pages) == 1
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    assert "Operations Manager at Example Ltd" in text
    assert "My verified background includes Excel." in text
