// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

import { POST } from "@/app/api/jobs/search-tasks/route";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("asynchronous job search route", () => {
  it("forwards the idempotency key to the fixed API endpoint", async () => {
    vi.stubEnv("SOLARAHIRE_API_URL", "https://api.example.test/");
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json(
        {
          task_id: "20fe7844-bfdb-4a2e-ae32-13ae7426e969",
          access_token: "opaque-token",
          status: "queued",
        },
        { status: 202 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const body = JSON.stringify({ role: "AI Engineer", location: "India" });

    const response = await POST(
      new Request("http://localhost/api/jobs/search-tasks", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": "browser-search-123",
        },
        body,
      }),
    );

    expect(response.status).toBe(202);
    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.example.test/api/v1/jobs/search-tasks",
      expect.objectContaining({
        headers: expect.objectContaining({
          "Idempotency-Key": "browser-search-123",
        }),
      }),
    );
  });
});
