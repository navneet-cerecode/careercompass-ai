import { forwardAuthenticatedRequest } from "@/lib/api/authenticated-proxy";

export const runtime = "nodejs";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function notFound() {
  return Response.json(
    {
      code: "job_not_found",
      message: "The requested job was not found.",
    },
    { status: 404, headers: { "Cache-Control": "no-store" } },
  );
}

async function forwardSavedJob(
  request: Request,
  context: { params: Promise<{ jobId: string }> },
  method: "PUT" | "DELETE",
) {
  const { jobId } = await context.params;
  if (!UUID_PATTERN.test(jobId)) {
    return notFound();
  }
  return forwardAuthenticatedRequest(request, {
    path: `/api/v1/saved-jobs/${jobId}`,
    method,
  });
}

export async function PUT(
  request: Request,
  context: { params: Promise<{ jobId: string }> },
) {
  return forwardSavedJob(request, context, "PUT");
}

export async function DELETE(
  request: Request,
  context: { params: Promise<{ jobId: string }> },
) {
  return forwardSavedJob(request, context, "DELETE");
}
