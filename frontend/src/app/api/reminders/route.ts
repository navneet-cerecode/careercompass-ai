import { forwardAuthenticatedRequest } from "@/lib/api/authenticated-proxy";

export const runtime = "nodejs";

export async function GET(request: Request) {
  return forwardAuthenticatedRequest(request, {
    path: "/api/v1/reminders",
    method: "GET",
    unavailableCode: "reminders_unavailable",
    unavailableMessage:
      "Your application reminders are temporarily unavailable. Try again shortly.",
  });
}
