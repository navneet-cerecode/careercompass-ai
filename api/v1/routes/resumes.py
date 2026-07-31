"""Resume API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from api.dependencies import (
    get_resume_extractor,
    get_resume_parser,
    get_settings,
)
from api.errors import ErrorResponse
from api.mappers import map_parsed_resume
from api.schemas.resumes import ParsedResumeResponse
from api.services.resume_upload import parse_resume_upload
from core.config import Settings
from services.resume.extractor import ResumeExtractor
from services.resume.parser_service import ResumeParserService

router = APIRouter()
SettingsDependency = Annotated[Settings, Depends(get_settings)]
ParserDependency = Annotated[ResumeParserService, Depends(get_resume_parser)]
ExtractorDependency = Annotated[ResumeExtractor, Depends(get_resume_extractor)]

ERROR_RESPONSES = {
    413: {"model": ErrorResponse},
    415: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}


@router.post(
    "/parse",
    response_model=ParsedResumeResponse,
    responses=ERROR_RESPONSES,
    summary="Parse a resume",
)
async def parse_resume(
    settings: SettingsDependency,
    parser: ParserDependency,
    extractor: ExtractorDependency,
    file: Annotated[UploadFile, File(description="PDF, DOCX, or UTF-8 text resume")],
) -> ParsedResumeResponse:
    resume = await parse_resume_upload(
        file,
        max_bytes=settings.max_resume_upload_bytes,
        parser=parser,
        extractor=extractor,
    )
    return map_parsed_resume(resume)
