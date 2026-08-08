from database.base import Base
from database.repositories.subscriptions import SubscriptionRepository
from database.repositories.users import UserRepository
from database.session import Database
from models.enums import SubscriptionPlan, SubscriptionStatus


def test_free_subscription_is_created_once_with_effective_entitlements():
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    with database.session() as session:
        user = UserRepository(session).create(email="owner@example.com", name="Owner")
        repository = SubscriptionRepository(session)

        first = repository.get_or_create_free(user_id=user.id)
        repeated = repository.get_or_create_free(user_id=user.id)

        assert repeated.id == first.id
        assert first.plan == SubscriptionPlan.FREE
        assert first.status == SubscriptionStatus.ACTIVE
        entitlements = repository.entitlements(first)
        assert entitlements.application_tracking is True
        assert entitlements.reminders is True
        assert entitlements.job_discovery is True
        assert entitlements.explainable_recommendations is True
        assert entitlements.tailored_documents is True
