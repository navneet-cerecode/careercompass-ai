import { describe, expect, it } from "vitest";

import {
  correlatedResponseHeaders,
  createRequestId,
} from "@/lib/api/request-correlation";

describe("request correlation", () => {
  it("creates opaque IDs and prefers an upstream correlation response", () => {
    const requestId = createRequestId();
    const upstream = Response.json({}, { headers: { "X-Request-ID": "api-request-1" } });

    expect(requestId).toMatch(/^[0-9a-f-]{36}$/);
    expect(correlatedResponseHeaders(requestId, upstream)).toEqual({
      "Cache-Control": "no-store",
      "X-Request-ID": "api-request-1",
    });
  });
});
