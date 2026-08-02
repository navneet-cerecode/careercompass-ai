import "server-only";

import { getApiBaseUrl } from "@/lib/api/config";
import {
  attachSessionHeaders,
  resolveApiIdentity,
  type ApiIdentity,
} from "@/lib/auth/session";

type AuthenticatedProxyOptions = {
  path: string;
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  timeoutMs?: number;
  maxBytes?: number;
  unavailableCode?: string;
  unavailableMessage?: string;
};

function proxyError(status: number, code: string, message: string) {
  return Response.json(
    { code, message },
    { status, headers: { "Cache-Control": "no-store" } },
  );
}

export async function forwardAuthenticatedRequest(
  request: Request,
  options: AuthenticatedProxyOptions,
) {
  let identity: ApiIdentity;
  try {
    identity = await resolveApiIdentity(request);
  } catch {
    return proxyError(
      401,
      "authentication_expired",
      "Your secure session could not be refreshed. Sign in again.",
    );
  }
  if (!identity.authorization) {
    return proxyError(
      401,
      "authentication_required",
      "Sign in to use account features.",
    );
  }

  const headers = new Headers({
    Accept: "application/json",
    Authorization: identity.authorization,
  });
  let body: string | undefined;
  if (["POST", "PUT", "PATCH"].includes(options.method)) {
    if (
      !request.headers
        .get("content-type")
        ?.toLowerCase()
        .includes("application/json")
    ) {
      return attachSessionHeaders(
        proxyError(415, "json_required", "This request must use JSON."),
        identity,
      );
    }
    body = await request.text();
    const maxBytes = options.maxBytes ?? 4_096;
    if (new TextEncoder().encode(body).byteLength > maxBytes) {
      return attachSessionHeaders(
        proxyError(
          413,
          "request_too_large",
          "This request is larger than the supported limit.",
        ),
        identity,
      );
    }
    try {
      JSON.parse(body);
    } catch {
      return attachSessionHeaders(
        proxyError(400, "invalid_json", "The request contains invalid JSON."),
        identity,
      );
    }
    headers.set("Content-Type", "application/json");
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${getApiBaseUrl()}${options.path}`, {
      method: options.method,
      headers,
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(options.timeoutMs ?? 10_000),
    });
  } catch {
    return attachSessionHeaders(
      proxyError(
        503,
        options.unavailableCode ?? "saved_jobs_unavailable",
        options.unavailableMessage ??
          "Saved jobs are temporarily unavailable. Try again shortly.",
      ),
      identity,
    );
  }

  if (upstream.status === 204) {
    return attachSessionHeaders(
      new Response(null, {
        status: 204,
        headers: { "Cache-Control": "no-store" },
      }),
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
