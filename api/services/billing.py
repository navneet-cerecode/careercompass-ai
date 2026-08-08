"""Subscription summary service isolated from payment providers."""

from dataclasses import dataclass
from uuid import UUID

from database.repositories.subscriptions import SubscriptionRepository
from database.session import Database
from models.subscription import Entitlements, Subscription


@dataclass(frozen=True)
class BillingSummary:
    subscription: Subscription
    entitlements: Entitlements


class BillingService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def get_summary(self, *, user_id: UUID) -> BillingSummary:
        with self.database.session() as session:
            repository = SubscriptionRepository(session)
            subscription = repository.get_or_create_free(user_id=user_id)
            return BillingSummary(
                subscription=subscription,
                entitlements=repository.entitlements(subscription),
            )
