import pytest

from database.base import Base
from database.repositories.identities import IdentityLinkRequired, IdentityRepository
from database.repositories.users import UserRepository
from database.session import Database
from models.identity import VerifiedIdentity


def make_database():
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    return database


def identity(subject="subject-1", email="ada@example.com"):
    return VerifiedIdentity(
        issuer="https://identity.example.test/",
        subject=subject,
        email=email,
        name="Ada Lovelace",
    )


def test_verified_identity_provisions_one_stable_user():
    database = make_database()
    with database.session() as session:
        repository = IdentityRepository(session)
        first = repository.provision(identity())
        repeated = repository.provision(identity())

    assert repeated.user_id == first.user_id
    assert repeated.subject == first.subject


def test_identity_never_auto_links_an_existing_email():
    database = make_database()
    with database.session() as session:
        UserRepository(session).create(email="ada@example.com", name="Legacy Ada")

    with database.session() as session:
        with pytest.raises(IdentityLinkRequired):
            IdentityRepository(session).provision(identity())


def test_another_subject_cannot_claim_an_existing_identity_email():
    database = make_database()
    with database.session() as session:
        IdentityRepository(session).provision(identity())

    with database.session() as session:
        with pytest.raises(IdentityLinkRequired):
            IdentityRepository(session).provision(identity(subject="attacker-subject"))
