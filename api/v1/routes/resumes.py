"""Resume API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Request, UploadFile

from api.dependencies import (
    get_resume_extractor,
    get_resume_parser,
    get_settings,
    get_optional_principal,
    get_product_analytics,
    get_required_principal,
    get_database,
)
from api.errors import APIError, ErrorResponse
from api.mappers import map_parsed_resume, map_resume
from api.schemas.resumes import ParsedResumeResponse, ResumeResponse
from api.services.resume_profiles import ResumeProfileService
from api.services.resume_upload import parse_resume_upload
from core.config import Settings
from core.observability import ProductAnalytics, ProductEventName
from services.resume.extractor import ResumeExtractor
from services.resume.parser_service import ResumeParserService
from database.session import Database
from models.identity import AuthenticatedPrincipal

router = APIRouter()
SettingsDependency = Annotated[Settings, Depends(get_settings)]
ParserDependency = Annotated[ResumeParserService, Depends(get_resume_parser)]
ExtractorDependency = Annotated[ResumeExtractor, Depends(get_resume_extractor)]
OptionalPrincipalDependency = Annotated[
    AuthenticatedPrincipal | None,
    Depends(get_optional_principal),
]
PrincipalDependency = Annotated[
    AuthenticatedPrincipal,
    Depends(get_required_principal),
]
DatabaseDependency = Annotated[Database, Depends(get_database)]
AnalyticsDependency = Annotated[ProductAnalytics, Depends(get_product_analytics)]

ERROR_RESPONSES = {
    413: {"model": ErrorResponse},
    415: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}


@router.post(
    "/parse",
    response_model=ParsedResumeResponse,
    responses=ERROR_RESPONSES,
    openapi_extra={"security": [{}, {"HTTPBearer": []}]},
    summary="Parse a resume",
)
async def parse_resume(
    http_request: Request,
    settings: SettingsDependency,
    parser: ParserDependency,
    extractor: ExtractorDependency,
    analytics: AnalyticsDependency,
    principal: OptionalPrincipalDependency,
    file: Annotated[UploadFile, File(description="PDF, DOCX, or UTF-8 text resume")],
) -> ParsedResumeResponse:
    original_filename = file.filename
    resume = await parse_resume_upload(
        file,
        max_bytes=settings.max_resume_upload_bytes,
        parser=parser,
        extractor=extractor,
    )
    if principal is not None:
        resume = ResumeProfileService(get_database(http_request)).save(
            user_id=principal.user_id,
            resume=resume,
            original_filename=original_filename,
        )
    analytics.track(
        ProductEventName.RESUME_PARSED,
        user_id=principal.user_id if principal is not None else None,
        properties={"authenticated": principal is not None},
    )
    return map_parsed_resume(resume)


@router.get(
    "/current",
    response_model=ResumeResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Get the signed-in user's current resume profile",
)
def get_current_resume(
    principal: PrincipalDependency,
    database: DatabaseDependency,
) -> ResumeResponse:
    resume = ResumeProfileService(database).get_current(user_id=principal.user_id)
    if resume is None:
        raise APIError(404, "resume_not_found", "No current resume profile was found.")
    return map_resume(resume)
