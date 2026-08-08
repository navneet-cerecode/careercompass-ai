import { forwardAuthenticatedRequest } from "@/lib/api/authenticated-proxy";

export const runtime = "nodejs";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export async function POST(
  request: Request,
  context: { params: Promise<{ coverLetterId: string }> },
) {
  const { coverLetterId } = await context.params;
  if (!UUID_PATTERN.test(coverLetterId)) {
    return Response.json(
      { code: "cover_letter_not_found", message: "The cover letter was not found." },
      { status: 404 },
    );
  }
  return forwardAuthenticatedRequest(request, {
    path: `/api/v1/cover-letters/${coverLetterId}/revisions`,
    method: "POST",
    maxBytes: 16_384,
  });
}
