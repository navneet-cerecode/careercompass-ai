"""Authenticated in-app application reminder endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from api.dependencies import get_application_reminder_service, get_required_principal
from api.errors import APIError, ErrorResponse
from api.mappers import map_job
from api.schemas.reminders import (
    ApplicationReminderListResponse,
    ApplicationReminderResponse,
    UpdateApplicationReminderRequest,
)
from api.services.reminders import ApplicationReminderService, ApplicationReminderSnapshot
from models.identity import AuthenticatedPrincipal

router = APIRouter()
PrincipalDependency = Annotated[
    AuthenticatedPrincipal,
    Depends(get_required_principal),
]
ReminderServiceDependency = Annotated[
    ApplicationReminderService,
    Depends(get_application_reminder_service),
]


def _map_reminder(snapshot: ApplicationReminderSnapshot) -> ApplicationReminderResponse:
    reminder = snapshot.reminder
    return ApplicationReminderResponse(
        id=reminder.id,
        application_id=reminder.application_id,
        job=map_job(snapshot.job),
        application_status=snapshot.application.status,
        next_action=reminder.next_action,
        due_at=reminder.due_at,
        status=reminder.status,
        read_at=reminder.read_at,
        dismissed_at=reminder.dismissed_at,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
    )


@router.get(
    "",
    response_model=ApplicationReminderListResponse,
    responses={401: {"model": ErrorResponse}},
    summary="List active reminders for the current account",
)
def list_application_reminders(
    principal: PrincipalDependency,
    reminders: ReminderServiceDependency,
) -> ApplicationReminderListResponse:
    return ApplicationReminderListResponse(
        items=tuple(
            _map_reminder(snapshot) for snapshot in reminders.list(user_id=principal.user_id)
        )
    )


@router.patch(
    "/{reminder_id}",
    response_model=ApplicationReminderResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Update an in-app reminder's user-controlled state",
)
def update_application_reminder(
    reminder_id: UUID,
    request: UpdateApplicationReminderRequest,
    principal: PrincipalDependency,
    reminders: ReminderServiceDependency,
) -> ApplicationReminderResponse:
    snapshot = reminders.set_status(
        user_id=principal.user_id,
        reminder_id=reminder_id,
        status=request.status,
    )
    if snapshot is None:
        raise APIError(
            404,
            "application_reminder_not_found",
            "The requested reminder was not found.",
        )
    return _map_reminder(snapshot)
