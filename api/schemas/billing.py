"""Authenticated subscription and entitlement contracts."""

from datetime import datetime

from api.schemas.common import APIModel
from models.enums import SubscriptionPlan, SubscriptionStatus


class EntitlementsResponse(APIModel):
    job_discovery: bool
    explainable_recommendations: bool
    tailored_documents: bool
    application_tracking: bool
    reminders: bool


class BillingSummaryResponse(APIModel):
    plan: SubscriptionPlan
    status: SubscriptionStatus
    provider: str | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool
    entitlements: EntitlementsResponse
    checkout_available: bool = False
