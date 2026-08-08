"""Review-first application packet orchestration."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from database.repositories.application_packets import (
    ApplicationPacketLocked,
    ApplicationPacketRepository,
)
from database.repositories.applications import ApplicationRepository
from database.repositories.cover_letters import CoverLetterRepository
from database.repositories.resumes import ResumeRepository
from database.repositories.tailored_resumes import TailoredResumeRepository
from database.session import Database
from models.application import JobApplication
from models.application_packet import ApplicationPacket
from models.enums import ApplicationStatus

PacketBlocker = Literal[
    "resume_missing",
    "job_details_not_reviewed",
    "resume_not_reviewed",
    "cover_letter_not_reviewed",
    "employer_questions_not_reviewed",
]


class ApplicationPacketNotFound(Exception):
    """Raised when an owner-scoped application or packet is unavailable."""


class ApplicationPacketInvalidDocument(Exception):
    """Raised when a selected document is unverified or targets another job."""


class ApplicationPacketIncomplete(Exception):
    def __init__(self, blockers: tuple[PacketBlocker, ...]) -> None:
        self.blockers = blockers
        super().__init__("The application packet still has required review steps.")


class ApplicationPacketInvalidStatus(Exception):
    """Raised when packet actions do not match the application lifecycle."""


@dataclass(frozen=True)
class ApplicationDocumentOption:
    id: UUID
    version: int
    source_resume_id: UUID
    approved_at: datetime


@dataclass(frozen=True)
class ApplicationPacketSnapshot:
    packet: ApplicationPacket
    application: JobApplication
    blockers: tuple[PacketBlocker, ...]
    tailored_resumes: tuple[ApplicationDocumentOption, ...]
    cover_letters: tuple[ApplicationDocumentOption, ...]


class ApplicationPacketService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, *, user_id: UUID, application_id: UUID) -> ApplicationPacketSnapshot:
        try:
            with self.database.session() as session:
                application = ApplicationRepository(session).get(
                    user_id=user_id,
                    application_id=application_id,
                )
                if application is None:
                    raise ApplicationPacketNotFound
                source_resume_id = application.resume_id
                if source_resume_id is None:
                    active_resume = ResumeRepository(session).get_active(user_id=user_id)
                    source_resume_id = active_resume.resume.id if active_resume else None
                packet = ApplicationPacketRepository(session).get_or_create(
                    user_id=user_id,
                    application_id=application_id,
                    source_resume_id=source_resume_id,
                )
                if packet is None:
                    raise ApplicationPacketNotFound
                return self._snapshot(session, packet=packet, application=application)
        except IntegrityError:
            # Concurrent first opens race on the unique application key. The winner's
            # packet is the idempotent result once its transaction commits.
            return self.get(user_id=user_id, application_id=application_id)

    def get(self, *, user_id: UUID, application_id: UUID) -> ApplicationPacketSnapshot:
        with self.database.session() as session:
            application = ApplicationRepository(session).get(
                user_id=user_id,
                application_id=application_id,
            )
            packet = ApplicationPacketRepository(session).get(
                user_id=user_id,
                application_id=application_id,
            )
            if application is None or packet is None:
                raise ApplicationPacketNotFound
            return self._snapshot(session, packet=packet, application=application)

    def update(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
        tailored_resume_id: UUID | None,
        cover_letter_id: UUID | None,
        job_details_reviewed: bool,
        resume_reviewed: bool,
        cover_letter_reviewed: bool,
        employer_questions_reviewed: bool,
    ) -> ApplicationPacketSnapshot:
        with self.database.session() as session:
            applications = ApplicationRepository(session)
            application = applications.get(user_id=user_id, application_id=application_id)
            packets = ApplicationPacketRepository(session)
            packet = packets.get(user_id=user_id, application_id=application_id)
            if application is None or packet is None:
                raise ApplicationPacketNotFound
            source_resume_id = self._validate_documents(
                session,
                user_id=user_id,
                job_id=application.job_id,
                current_source_resume_id=packet.source_resume_id,
                tailored_resume_id=tailored_resume_id,
                cover_letter_id=cover_letter_id,
            )
            try:
                updated = packets.update(
                    user_id=user_id,
                    application_id=application_id,
                    source_resume_id=source_resume_id,
                    tailored_resume_id=tailored_resume_id,
                    cover_letter_id=cover_letter_id,
                    job_details_reviewed=job_details_reviewed,
                    resume_reviewed=resume_reviewed,
                    cover_letter_reviewed=(
                        cover_letter_reviewed if cover_letter_id is not None else False
                    ),
                    employer_questions_reviewed=employer_questions_reviewed,
                )
            except ApplicationPacketLocked:
                raise
            if updated is None:
                raise ApplicationPacketNotFound
            return self._snapshot(session, packet=updated, application=application)

    def mark_ready(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
    ) -> ApplicationPacketSnapshot:
        with self.database.session() as session:
            applications = ApplicationRepository(session)
            packets = ApplicationPacketRepository(session)
            application = applications.get(user_id=user_id, application_id=application_id)
            packet = packets.get(user_id=user_id, application_id=application_id)
            if application is None or packet is None:
                raise ApplicationPacketNotFound
            if application.status not in {
                ApplicationStatus.PREPARING,
                ApplicationStatus.READY_TO_APPLY,
            }:
                raise ApplicationPacketInvalidStatus
            blockers = self._blockers(packet)
            if blockers:
                raise ApplicationPacketIncomplete(blockers)
            packet = packets.mark_ready(user_id=user_id, application_id=application_id)
            if packet is None:
                raise ApplicationPacketNotFound
            if application.status == ApplicationStatus.PREPARING:
                transitioned = applications.transition(
                    user_id=user_id,
                    application_id=application_id,
                    new_status=ApplicationStatus.READY_TO_APPLY,
                    note="Application packet reviewed and marked ready by the user.",
                    next_action="Complete the application on the employer site",
                    next_action_due_at=application.next_action_due_at,
                )
                if transitioned is None:
                    raise ApplicationPacketNotFound
                application = transitioned
            return self._snapshot(session, packet=packet, application=application)

    def confirm_submitted(
        self,
        *,
        user_id: UUID,
        application_id: UUID,
    ) -> ApplicationPacketSnapshot:
        with self.database.session() as session:
            applications = ApplicationRepository(session)
            packets = ApplicationPacketRepository(session)
            application = applications.get(user_id=user_id, application_id=application_id)
            packet = packets.get(user_id=user_id, application_id=application_id)
            if application is None or packet is None:
                raise ApplicationPacketNotFound
            if packet.ready_at is None:
                raise ApplicationPacketIncomplete(self._blockers(packet))
            if application.status != ApplicationStatus.READY_TO_APPLY:
                raise ApplicationPacketInvalidStatus
            transitioned = applications.transition(
                user_id=user_id,
                application_id=application_id,
                new_status=ApplicationStatus.APPLIED,
                note="User confirmed submission on the employer site.",
                next_action="Record the employer response",
            )
            if transitioned is None:
                raise ApplicationPacketNotFound
            return self._snapshot(session, packet=packet, application=transitioned)

    @staticmethod
    def _validate_documents(
        session,
        *,
        user_id: UUID,
        job_id: UUID,
        current_source_resume_id: UUID | None,
        tailored_resume_id: UUID | None,
        cover_letter_id: UUID | None,
    ) -> UUID | None:
        source_resume_id = current_source_resume_id
        if tailored_resume_id is not None:
            tailored = TailoredResumeRepository(session).get(
                user_id=user_id,
                tailored_resume_id=tailored_resume_id,
            )
            if (
                tailored is None
                or tailored.job_id != job_id
                or tailored.verification_status != "user_verified"
                or (
                    source_resume_id is not None
                    and tailored.source_resume_id != source_resume_id
                )
            ):
                raise ApplicationPacketInvalidDocument
            source_resume_id = tailored.source_resume_id
        if cover_letter_id is not None:
            cover_letter = CoverLetterRepository(session).get(
                user_id=user_id,
                cover_letter_id=cover_letter_id,
            )
            if (
                cover_letter is None
                or cover_letter.job_id != job_id
                or cover_letter.verification_status != "user_verified"
                or (
                    source_resume_id is not None
                    and cover_letter.source_resume_id != source_resume_id
                )
            ):
                raise ApplicationPacketInvalidDocument
            source_resume_id = cover_letter.source_resume_id
        if source_resume_id is not None and ResumeRepository(session).get(
            user_id=user_id,
            resume_id=source_resume_id,
        ) is None:
            raise ApplicationPacketInvalidDocument
        return source_resume_id

    @classmethod
    def _snapshot(
        cls,
        session,
        *,
        packet: ApplicationPacket,
        application: JobApplication,
    ) -> ApplicationPacketSnapshot:
        tailored_resumes = tuple(
            ApplicationDocumentOption(
                id=item.id,
                version=item.version,
                source_resume_id=item.source_resume_id,
                approved_at=item.approved_at,
            )
            for item in TailoredResumeRepository(session).list_verified_for_job(
                user_id=application.user_id,
                job_id=application.job_id,
            )
            if item.approved_at is not None
            and (
                packet.source_resume_id is None
                or item.source_resume_id == packet.source_resume_id
            )
        )
        cover_letters = tuple(
            ApplicationDocumentOption(
                id=item.id,
                version=item.version,
                source_resume_id=item.source_resume_id,
                approved_at=item.approved_at,
            )
            for item in CoverLetterRepository(session).list_verified_for_job(
                user_id=application.user_id,
                job_id=application.job_id,
            )
            if item.approved_at is not None
            and (
                packet.source_resume_id is None
                or item.source_resume_id == packet.source_resume_id
            )
        )
        return ApplicationPacketSnapshot(
            packet=packet,
            application=application,
            blockers=cls._blockers(packet),
            tailored_resumes=tailored_resumes,
            cover_letters=cover_letters,
        )

    @staticmethod
    def _blockers(packet: ApplicationPacket) -> tuple[PacketBlocker, ...]:
        blockers: list[PacketBlocker] = []
        if packet.source_resume_id is None:
            blockers.append("resume_missing")
        if not packet.job_details_reviewed:
            blockers.append("job_details_not_reviewed")
        if not packet.resume_reviewed:
            blockers.append("resume_not_reviewed")
        if packet.cover_letter_id is not None and not packet.cover_letter_reviewed:
            blockers.append("cover_letter_not_reviewed")
        if not packet.employer_questions_reviewed:
            blockers.append("employer_questions_not_reviewed")
        return tuple(blockers)
