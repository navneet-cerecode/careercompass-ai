import { getApiBaseUrl } from "@/lib/api/config";
import {
  attachSessionHeaders,
  resolveApiIdentity,
} from "@/lib/auth/session";

export const runtime = "nodejs";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function proxyError(status: number, code: string, message: string) {
  return Response.json(
    { code, message },
    { status, headers: { "Cache-Control": "no-store" } },
  );
}

async function forwardTaskRequest(
  request: Request,
  context: { params: Promise<{ taskId: string }> },
  method: "GET" | "DELETE",
) {
  const { taskId } = await context.params;
  const token = request.headers.get("x-task-token");
  if (!UUID_PATTERN.test(taskId) || !token || token.length > 200) {
    return proxyError(404, "task_not_found", "The requested task was not found.");
  }

  let identity;
  try {
    identity = await resolveApiIdentity(request);
  } catch {
    return proxyError(
      401,
      "authentication_expired",
      "Your secure session could not be refreshed. Sign in again.",
    );
  }

  const headers = new Headers({
    Accept: "application/json",
    "X-Task-Token": token,
  });
  if (identity.authorization) {
    headers.set("Authorization", identity.authorization);
  }

  let upstream: Response;
  try {
    upstream = await fetch(
      `${getApiBaseUrl()}/api/v1/jobs/search-tasks/${taskId}`,
      {
        method,
        headers,
        cache: "no-store",
        signal: AbortSignal.timeout(10_000),
      },
    );
  } catch {
    return attachSessionHeaders(
      proxyError(
        503,
        "job_search_unavailable",
        "Job search is temporarily unavailable. Try again shortly.",
      ),
      identity,
    );
  }
  if (
    !upstream.headers
      .get("content-type")
      ?.toLowerCase()
      .includes("application/json")
  ) {
    return attachSessionHeaders(
      proxyError(
        502,
        "invalid_service_response",
        "The career service returned an unexpected response.",
      ),
      identity,
    );
  }
  try {
    return attachSessionHeaders(
      Response.json(await upstream.json(), {
        status: upstream.status,
        headers: { "Cache-Control": "no-store" },
      }),
      identity,
    );
  } catch {
    return attachSessionHeaders(
      proxyError(
        502,
        "invalid_service_response",
        "The career service returned an unexpected response.",
      ),
      identity,
    );
  }
}

export async function GET(
  request: Request,
  context: { params: Promise<{ taskId: string }> },
) {
  return forwardTaskRequest(request, context, "GET");
}

export async function DELETE(
  request: Request,
  context: { params: Promise<{ taskId: string }> },
) {
  return forwardTaskRequest(request, context, "DELETE");
}
