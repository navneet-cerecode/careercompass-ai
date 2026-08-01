"""Provision verified external identities without storing credentials."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.models.identities import UserIdentityRecord
from database.models.users import UserRecord
from models.identity import AuthenticatedPrincipal, VerifiedIdentity


class IdentityLinkRequired(ValueError):
    """Raised when a verified email belongs to an unlinked account."""


class IdentityRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def provision(self, identity: VerifiedIdentity) -> AuthenticatedPrincipal:
        record = self._get_identity(identity)
        if record is not None:
            return self._refresh(record, identity)

        email = str(identity.email).casefold()
        if self.session.scalar(select(UserRecord).where(UserRecord.email == email)):
            raise IdentityLinkRequired(
                "A matching email exists but has not been safely linked to this identity."
            )

        user = UserRecord(
            email=email,
            name=identity.name.strip(),
        )
        try:
            with self.session.begin_nested():
                self.session.add(user)
                self.session.flush()
                record = UserIdentityRecord(
                    user_id=user.id,
                    issuer=identity.issuer,
                    subject=identity.subject,
                    email_at_provision=email,
                )
                self.session.add(record)
                self.session.flush()
        except IntegrityError:
            existing = self._get_identity(identity)
            if existing is None:
                raise
            return self._refresh(existing, identity)
        return self._to_principal(record, user)

    def _get_identity(
        self,
        identity: VerifiedIdentity,
    ) -> UserIdentityRecord | None:
        return self.session.scalar(
            select(UserIdentityRecord).where(
                UserIdentityRecord.issuer == identity.issuer,
                UserIdentityRecord.subject == identity.subject,
            )
        )

    def _refresh(
        self,
        record: UserIdentityRecord,
        identity: VerifiedIdentity,
    ) -> AuthenticatedPrincipal:
        user = self.session.get(UserRecord, record.user_id)
        if user is None:
            raise ValueError("Identity owner does not exist.")
        email = str(identity.email).casefold()
        email_owner = self.session.scalar(
            select(UserRecord).where(
                UserRecord.email == email,
                UserRecord.id != user.id,
            )
        )
        if email_owner is not None:
            raise IdentityLinkRequired("The verified email is already used by another account.")
        user.email = email
        user.name = identity.name.strip()
        record.last_authenticated_at = datetime.now(timezone.utc)
        self.session.flush()
        return self._to_principal(record, user)

    @staticmethod
    def _to_principal(
        identity: UserIdentityRecord,
        user: UserRecord,
    ) -> AuthenticatedPrincipal:
        return AuthenticatedPrincipal(
            user_id=user.id,
            issuer=identity.issuer,
            subject=identity.subject,
            email=user.email,
            name=user.name,
        )
