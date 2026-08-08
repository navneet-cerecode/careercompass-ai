"""Provider-neutral subscriptions and effective product entitlements."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from models.enums import SubscriptionPlan, SubscriptionStatus


class Subscription(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    user_id: UUID
    plan: SubscriptionPlan
    status: SubscriptionStatus
    provider: str | None = None
    external_customer_id: str | None = None
    external_subscription_id: str | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False
    created_at: datetime
    updated_at: datetime


class Entitlements(BaseModel):
    model_config = ConfigDict(frozen=True)

    plan: SubscriptionPlan
    job_discovery: bool
    explainable_recommendations: bool
    tailored_documents: bool
    application_tracking: bool
    reminders: bool
