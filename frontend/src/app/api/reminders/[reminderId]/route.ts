import { forwardAuthenticatedRequest } from "@/lib/api/authenticated-proxy";

export const runtime = "nodejs";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function notFound() {
  return Response.json(
    {
      code: "application_reminder_not_found",
      message: "The requested reminder was not found.",
    },
    { status: 404, headers: { "Cache-Control": "no-store" } },
  );
}

export async function PATCH(
  request: Request,
  context: { params: Promise<{ reminderId: string }> },
) {
  const { reminderId } = await context.params;
  if (!UUID_PATTERN.test(reminderId)) return notFound();
  return forwardAuthenticatedRequest(request, {
    path: `/api/v1/reminders/${reminderId}`,
    method: "PATCH",
    maxBytes: 256,
    unavailableCode: "reminders_unavailable",
    unavailableMessage:
      "Your application reminders are temporarily unavailable. Try again shortly.",
  });
}
