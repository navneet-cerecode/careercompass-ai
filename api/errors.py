"""Stable application error contract and FastAPI handler."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.schemas.common import APIModel


class ValidationIssue(APIModel):
    location: tuple[str | int, ...]
    message: str
    type: str


class ErrorResponse(APIModel):
    code: str
    message: str
    details: tuple[ValidationIssue, ...] = ()


class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


async def api_error_handler(_: Request, error: APIError) -> JSONResponse:
    payload = ErrorResponse(code=error.code, message=error.message)
    return JSONResponse(
        status_code=error.status_code,
        content=payload.model_dump(mode="json", exclude_defaults=True),
    )


async def request_validation_error_handler(
    _: Request,
    error: RequestValidationError,
) -> JSONResponse:
    payload = ErrorResponse(
        code="request_validation_failed",
        message="The request did not pass validation.",
        details=tuple(
            ValidationIssue(
                location=tuple(issue["loc"]),
                message=issue["msg"],
                type=issue["type"],
            )
            for issue in error.errors()
        ),
    )
    return JSONResponse(
        status_code=422,
        content=payload.model_dump(mode="json", exclude_defaults=True),
    )
