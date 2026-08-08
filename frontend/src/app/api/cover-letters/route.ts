import { forwardAuthenticatedRequest } from "@/lib/api/authenticated-proxy";

export const runtime = "nodejs";

export async function POST(request: Request) {
  return forwardAuthenticatedRequest(request, {
    path: "/api/v1/cover-letters",
    method: "POST",
    unavailableCode: "cover_letter_unavailable",
    unavailableMessage:
      "The cover letter workspace is temporarily unavailable. Try again shortly.",
  });
}
