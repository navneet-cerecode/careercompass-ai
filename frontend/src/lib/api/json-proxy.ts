import "server-only";

import { getApiBaseUrl } from "@/lib/api/config";
import {
  attachSessionHeaders,
  resolveApiIdentity,
  type ApiIdentity,
} from "@/lib/auth/session";

type JsonProxyOptions = {
  path: string;
  timeoutMs: number;
  maxBytes: number;
  serviceName: string;
  forwardedHeaders?: string[];
  forwardIdentity?: boolean;
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

  const headers: Record<string, string> = {
    Accept: "application/json",
    "Content-Type": "application/json",
  };
  let identity: ApiIdentity = {
    authorization: null,
    sessionHeaders: new Headers(),
  };
  if (options.forwardIdentity) {
    try {
      identity = await resolveApiIdentity(request);
    } catch {
      return errorResponse(
        401,
        "authentication_expired",
        "Your secure session could not be refreshed. Sign in again.",
      );
    }
    if (identity.authorization) {
      headers.Authorization = identity.authorization;
    }
  }
  for (const name of options.forwardedHeaders ?? []) {
    const value = request.headers.get(name);
    if (value) {
      headers[name] = value;
    }
  }

  let upstreamResponse: Response;
  try {
    upstreamResponse = await fetch(`${getApiBaseUrl()}${options.path}`, {
      method: "POST",
      headers,
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(options.timeoutMs),
    });
  } catch {
    return attachSessionHeaders(
      errorResponse(
        503,
        `${options.serviceName}_unavailable`,
        `${options.serviceName === "job_search" ? "Job search" : "Recommendations"} are temporarily unavailable. Try again shortly.`,
      ),
      identity,
    );
  }

  if (
    !upstreamResponse.headers
      .get("content-type")
      ?.toLowerCase()
      .includes("application/json")
  ) {
    return attachSessionHeaders(
      errorResponse(
        502,
        "invalid_service_response",
        "The career service returned an unexpected response.",
      ),
      identity,
    );
  }

  try {
    const payload: unknown = await upstreamResponse.json();
    return attachSessionHeaders(
      Response.json(payload, {
        status: upstreamResponse.status,
        headers: { "Cache-Control": "no-store" },
      }),
      identity,
    );
  } catch {
    return attachSessionHeaders(
      errorResponse(
        502,
        "invalid_service_response",
        "The career service returned an unexpected response.",
      ),
      identity,
    );
  }
}
