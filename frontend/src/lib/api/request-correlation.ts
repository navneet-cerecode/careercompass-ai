export function createRequestId() {
  return crypto.randomUUID();
}

export function correlatedResponseHeaders(
  requestId: string,
  upstream?: Response,
) {
  return {
    "Cache-Control": "no-store",
    "X-Request-ID": upstream?.headers.get("x-request-id") ?? requestId,
  };
}
