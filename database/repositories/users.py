"""User ownership repository without authentication concerns."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.users import UserRecord


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    name: str
    is_active: bool


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, email: str, name: str) -> User:
        normalized_email = email.strip().casefold()
        normalized_name = name.strip()
        if not normalized_email or not normalized_name:
            raise ValueError("User email and name are required.")
        if self.get_by_email(normalized_email) is not None:
            raise ValueError("A user with this email already exists.")

        record = UserRecord(email=normalized_email, name=normalized_name)
        self.session.add(record)
        self.session.flush()
        return self._to_domain(record)

    def get(self, user_id: UUID) -> User | None:
        record = self.session.get(UserRecord, user_id)
        return self._to_domain(record) if record is not None else None

    def get_by_email(self, email: str) -> User | None:
        record = self.session.scalar(
            select(UserRecord).where(UserRecord.email == email.strip().casefold())
        )
        return self._to_domain(record) if record is not None else None

    @staticmethod
    def _to_domain(record: UserRecord) -> User:
        return User(
            id=record.id,
            email=record.email,
            name=record.name,
            is_active=record.is_active,
        )
