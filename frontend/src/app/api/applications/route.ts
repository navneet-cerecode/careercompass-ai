import { forwardAuthenticatedRequest } from "@/lib/api/authenticated-proxy";

export const runtime = "nodejs";

const unavailable = {
  unavailableCode: "applications_unavailable",
  unavailableMessage:
    "Your application tracker is temporarily unavailable. Try again shortly.",
};

export async function GET(request: Request) {
  return forwardAuthenticatedRequest(request, {
    path: "/api/v1/applications",
    method: "GET",
    ...unavailable,
  });
}

export async function POST(request: Request) {
  return forwardAuthenticatedRequest(request, {
    path: "/api/v1/applications",
    method: "POST",
    maxBytes: 8_192,
    ...unavailable,
  });
}
