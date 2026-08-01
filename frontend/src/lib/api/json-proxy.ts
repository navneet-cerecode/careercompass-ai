import "server-only";

import { getApiBaseUrl } from "@/lib/api/config";

type JsonProxyOptions = {
  path: string;
  timeoutMs: number;
  maxBytes: number;
  serviceName: string;
};

function errorResponse(status: number, code: string, message: string) {
  return Response.json(
    { code, message },
    {
      status,
      headers: { "Cache-Control": "no-store" },
    },
  );
}

export async function forwardJsonRequest(
  request: Request,
  options: JsonProxyOptions,
) {
  if (
    !request.headers
      .get("content-type")
      ?.toLowerCase()
      .includes("application/json")
  ) {
    return errorResponse(
      415,
      "json_required",
      "This request must use JSON.",
    );
  }

  const contentLength = Number(request.headers.get("content-length"));
  if (Number.isFinite(contentLength) && contentLength > options.maxBytes) {
    return errorResponse(
      413,
      "request_too_large",
      "This request is larger than the supported limit.",
    );
  }

  let body: string;
  try {
    body = await request.text();
    if (new TextEncoder().encode(body).byteLength > options.maxBytes) {
      return errorResponse(
        413,
        "request_too_large",
        "This request is larger than the supported limit.",
      );
    }
    JSON.parse(body);
  } catch {
    return errorResponse(400, "invalid_json", "The request contains invalid JSON.");
  }

  let upstreamResponse: Response;
  try {
    upstreamResponse = await fetch(`${getApiBaseUrl()}${options.path}`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(options.timeoutMs),
    });
  } catch {
    return errorResponse(
      503,
      `${options.serviceName}_unavailable`,
      `${options.serviceName === "job_search" ? "Job search" : "Recommendations"} are temporarily unavailable. Try again shortly.`,
    );
  }

  if (
    !upstreamResponse.headers
      .get("content-type")
      ?.toLowerCase()
      .includes("application/json")
  ) {
    return errorResponse(
      502,
      "invalid_service_response",
      "The career service returned an unexpected response.",
    );
  }

  try {
    const payload: unknown = await upstreamResponse.json();
    return Response.json(payload, {
      status: upstreamResponse.status,
      headers: { "Cache-Control": "no-store" },
    });
  } catch {
    return errorResponse(
      502,
      "invalid_service_response",
      "The career service returned an unexpected response.",
    );
  }
}
