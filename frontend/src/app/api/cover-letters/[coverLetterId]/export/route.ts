import { forwardAuthenticatedRequest } from "@/lib/api/authenticated-proxy";

export const runtime = "nodejs";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export async function GET(
  request: Request,
  context: { params: Promise<{ coverLetterId: string }> },
) {
  const { coverLetterId } = await context.params;
  const format = new URL(request.url).searchParams.get("format");
  if (!UUID_PATTERN.test(coverLetterId) || !["pdf", "docx"].includes(format ?? "")) {
    return Response.json(
      { code: "invalid_export_request", message: "Choose a valid cover letter format." },
      { status: 400 },
    );
  }
  return forwardAuthenticatedRequest(request, {
    path: `/api/v1/cover-letters/${coverLetterId}/export?format=${format}`,
    method: "GET",
    responseMode: "binary",
    unavailableCode: "cover_letter_export_unavailable",
    unavailableMessage: "Cover letter export is temporarily unavailable. Try again shortly.",
  });
}
