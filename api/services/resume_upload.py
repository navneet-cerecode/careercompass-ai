"""Bounded upload handling for resume parsing."""

import tempfile
from pathlib import Path

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from api.errors import APIError
from models.resume import Resume
from services.resume.extractor import ResumeExtractor
from services.resume.parser_service import ResumeParserService

ALLOWED_CONTENT_TYPES = {
    ".pdf": {"application/pdf", "application/octet-stream"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    },
    ".txt": {"text/plain", "application/octet-stream"},
}


def _validate_file_content(extension: str, content: bytes) -> None:
    if not content:
        raise APIError(422, "empty_resume", "The uploaded resume is empty.")
    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise APIError(422, "invalid_resume", "The uploaded file is not a valid PDF.")
    if extension == ".docx" and not content.startswith(b"PK"):
        raise APIError(422, "invalid_resume", "The uploaded file is not a valid DOCX.")
    if extension == ".txt" and b"\x00" in content:
        raise APIError(422, "invalid_resume", "The uploaded text file contains binary data.")


async def parse_resume_upload(
    upload: UploadFile,
    *,
    max_bytes: int,
    parser: ResumeParserService,
    extractor: ResumeExtractor,
) -> Resume:
    filename = Path(upload.filename or "").name
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_CONTENT_TYPES:
        raise APIError(
            415,
            "unsupported_resume_type",
            "Resume files must use PDF, DOCX, or TXT format.",
        )

    if upload.content_type not in ALLOWED_CONTENT_TYPES[extension]:
        raise APIError(
            415,
            "resume_type_mismatch",
            "The resume content type does not match its filename.",
        )

    content = await upload.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise APIError(
            413,
            "resume_too_large",
            f"Resume files cannot exceed {max_bytes} bytes.",
        )

    _validate_file_content(extension, content)
    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as handle:
            temp_path = Path(handle.name)
            handle.write(content)

        text = await run_in_threadpool(parser.parse, str(temp_path))
        return await run_in_threadpool(extractor.extract, text)
    except APIError:
        raise
    except Exception as error:
        raise APIError(
            422,
            "resume_parse_failed",
            "The resume could not be parsed.",
        ) from error
    finally:
        await upload.close()
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
