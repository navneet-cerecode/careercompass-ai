import { forwardAuthenticatedRequest } from "@/lib/api/authenticated-proxy";

export const runtime = "nodejs";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export async function GET(
  request: Request,
  context: { params: Promise<{ tailoredResumeId: string }> },
) {
  const { tailoredResumeId } = await context.params;
  if (!UUID_PATTERN.test(tailoredResumeId)) {
    return Response.json(
      { code: "tailored_resume_not_found", message: "The tailored resume was not found." },
      { status: 404 },
    );
  }
  return forwardAuthenticatedRequest(request, {
    path: `/api/v1/tailored-resumes/${tailoredResumeId}/versions`,
    method: "GET",
  });
}
