import pytest

from services.resume.parser_service import ResumeParserService


def test_parser_service_reads_utf8_text_file(tmp_path):
    resume_path = tmp_path / "resume.txt"
    resume_path.write_text("Ada Lovelace\nPython engineer", encoding="utf-8")

    text = ResumeParserService().parse(str(resume_path))

    assert text == "Ada Lovelace\nPython engineer"


def test_parser_service_rejects_unsupported_extension(tmp_path):
    resume_path = tmp_path / "resume.rtf"
    resume_path.write_text("unsupported", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file type"):
        ResumeParserService().parse(str(resume_path))


def test_parser_service_rejects_a_file_without_extractable_text(tmp_path):
    resume_path = tmp_path / "resume.txt"
    resume_path.write_text(" \n ", encoding="utf-8")

    with pytest.raises(ValueError, match="No text could be extracted"):
        ResumeParserService().parse(str(resume_path))
