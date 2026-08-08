import { forwardAuthenticatedRequest } from "@/lib/api/authenticated-proxy";

export const runtime = "nodejs";

export async function POST(request: Request) {
  return forwardAuthenticatedRequest(request, {
    path: "/api/v1/tailored-resumes",
    method: "POST",
    unavailableCode: "tailored_resume_unavailable",
    unavailableMessage:
      "The tailored resume workspace is temporarily unavailable. Try again shortly.",
  });
}
