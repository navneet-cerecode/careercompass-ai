"""Authenticated billing summary endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from api.dependencies import get_billing_service, get_product_analytics, get_required_principal
from api.errors import ErrorResponse
from api.schemas.billing import BillingSummaryResponse, EntitlementsResponse
from api.services.billing import BillingService
from models.identity import AuthenticatedPrincipal
from core.observability import ProductAnalytics, ProductEventName

router = APIRouter()
PrincipalDependency = Annotated[
    AuthenticatedPrincipal,
    Depends(get_required_principal),
]
BillingServiceDependency = Annotated[BillingService, Depends(get_billing_service)]
AnalyticsDependency = Annotated[ProductAnalytics, Depends(get_product_analytics)]


@router.get(
    "/summary",
    response_model=BillingSummaryResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Get the current account's plan and effective entitlements",
)
def get_billing_summary(
    principal: PrincipalDependency,
    billing: BillingServiceDependency,
    analytics: AnalyticsDependency,
) -> BillingSummaryResponse:
    summary = billing.get_summary(user_id=principal.user_id)
    subscription = summary.subscription
    response = BillingSummaryResponse(
        plan=subscription.plan,
        status=subscription.status,
        provider=subscription.provider,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        entitlements=EntitlementsResponse(**summary.entitlements.model_dump(exclude={"plan"})),
        checkout_available=False,
    )
    analytics.track(
        ProductEventName.BILLING_SUMMARY_VIEWED,
        user_id=principal.user_id,
        properties={"plan": subscription.plan.value, "status": subscription.status.value},
    )
    return response
