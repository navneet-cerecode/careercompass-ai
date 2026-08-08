"""Subscription persistence and deterministic entitlement resolution."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.subscriptions import SubscriptionRecord
from database.models.users import UserRecord
from models.enums import SubscriptionPlan, SubscriptionStatus
from models.subscription import Entitlements, Subscription

PLAN_ENTITLEMENTS: dict[SubscriptionPlan, Entitlements] = {
    SubscriptionPlan.FREE: Entitlements(
        plan=SubscriptionPlan.FREE,
        job_discovery=True,
        explainable_recommendations=True,
        tailored_documents=True,
        application_tracking=True,
        reminders=True,
    ),
    SubscriptionPlan.PRO: Entitlements(
        plan=SubscriptionPlan.PRO,
        job_discovery=True,
        explainable_recommendations=True,
        tailored_documents=True,
        application_tracking=True,
        reminders=True,
    ),
}


class SubscriptionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create_free(self, *, user_id: UUID) -> Subscription:
        record = self.session.scalar(
            select(SubscriptionRecord).where(SubscriptionRecord.user_id == user_id)
        )
        if record is None:
            if self.session.get(UserRecord, user_id) is None:
                raise ValueError("User does not exist.")
            record = SubscriptionRecord(
                user_id=user_id,
                plan=SubscriptionPlan.FREE.value,
                status=SubscriptionStatus.ACTIVE.value,
                cancel_at_period_end=False,
            )
            self.session.add(record)
            self.session.flush()
            self.session.refresh(record)
        return Subscription.model_validate(record, from_attributes=True)

    @staticmethod
    def entitlements(subscription: Subscription) -> Entitlements:
        effective_plan = (
            subscription.plan
            if subscription.status in {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING}
            else SubscriptionPlan.FREE
        )
        return PLAN_ENTITLEMENTS[effective_plan]
