import { forwardAuthenticatedRequest } from "@/lib/api/authenticated-proxy";

export const runtime = "nodejs";

export async function GET(request: Request) {
  return forwardAuthenticatedRequest(request, {
    path: "/api/v1/billing/summary",
    method: "GET",
    unavailableCode: "billing_unavailable",
    unavailableMessage:
      "Your plan details are temporarily unavailable. Try again shortly.",
  });
}
