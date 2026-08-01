import { getApiBaseUrl } from "@/lib/api/config";

export const runtime = "nodejs";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function proxyError(status: number, code: string, message: string) {
  return Response.json(
    { code, message },
    { status, headers: { "Cache-Control": "no-store" } },
  );
}

export async function GET(
  request: Request,
  context: { params: Promise<{ taskId: string }> },
) {
  const { taskId } = await context.params;
  const token = request.headers.get("x-task-token");
  if (!UUID_PATTERN.test(taskId) || !token || token.length > 200) {
    return proxyError(404, "task_not_found", "The requested task was not found.");
  }

  let upstream: Response;
  try {
    upstream = await fetch(
      `${getApiBaseUrl()}/api/v1/jobs/search-tasks/${taskId}`,
      {
        headers: {
          Accept: "application/json",
          "X-Task-Token": token,
        },
        cache: "no-store",
        signal: AbortSignal.timeout(10_000),
      },
    );
  } catch {
    return proxyError(
      503,
      "job_search_unavailable",
      "Job search is temporarily unavailable. Try again shortly.",
    );
  }
  if (
    !upstream.headers
      .get("content-type")
      ?.toLowerCase()
      .includes("application/json")
  ) {
    return proxyError(
      502,
      "invalid_service_response",
      "The career service returned an unexpected response.",
    );
  }
  try {
    return Response.json(await upstream.json(), {
      status: upstream.status,
      headers: { "Cache-Control": "no-store" },
    });
  } catch {
    return proxyError(
      502,
      "invalid_service_response",
      "The career service returned an unexpected response.",
    );
  }
}
