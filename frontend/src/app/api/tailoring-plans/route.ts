import { forwardAuthenticatedRequest } from "@/lib/api/authenticated-proxy";

export const runtime = "nodejs";

export async function POST(request: Request) {
  return forwardAuthenticatedRequest(request, {
    path: "/api/v1/tailoring-plans",
    method: "POST",
    unavailableCode: "tailoring_unavailable",
    unavailableMessage:
      "The factual tailoring workspace is temporarily unavailable. Try again shortly.",
  });
}
