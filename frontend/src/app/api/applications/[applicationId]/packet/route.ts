import { forwardAuthenticatedRequest } from "@/lib/api/authenticated-proxy";

export const runtime = "nodejs";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function notFound() {
  return Response.json(
    {
      code: "application_not_found",
      message: "The requested application was not found.",
    },
    { status: 404, headers: { "Cache-Control": "no-store" } },
  );
}

async function forward(
  request: Request,
  context: { params: Promise<{ applicationId: string }> },
  method: "GET" | "POST" | "PATCH",
) {
  const { applicationId } = await context.params;
  if (!UUID_PATTERN.test(applicationId)) return notFound();
  return forwardAuthenticatedRequest(request, {
    path: `/api/v1/applications/${applicationId}/packet`,
    method,
    ...(method === "GET" ? {} : { maxBytes: 8_192 }),
    unavailableCode: "application_packet_unavailable",
    unavailableMessage:
      "Your application packet is temporarily unavailable. Try again shortly.",
  });
}

export function GET(
  request: Request,
  context: { params: Promise<{ applicationId: string }> },
) {
  return forward(request, context, "GET");
}

export function POST(
  request: Request,
  context: { params: Promise<{ applicationId: string }> },
) {
  return forward(request, context, "POST");
}

export function PATCH(
  request: Request,
  context: { params: Promise<{ applicationId: string }> },
) {
  return forward(request, context, "PATCH");
}
