import { forwardAuthenticatedRequest } from "@/lib/api/authenticated-proxy";

export const runtime = "nodejs";

export function GET(request: Request) {
  return forwardAuthenticatedRequest(request, {
    path: "/api/v1/skill-intelligence",
    method: "GET",
    unavailableCode: "skill_intelligence_unavailable",
    unavailableMessage:
      "Your skill intelligence is temporarily unavailable. Try again shortly.",
  });
}
