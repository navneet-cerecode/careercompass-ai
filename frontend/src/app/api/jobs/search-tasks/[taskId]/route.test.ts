// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

import { DELETE, GET } from "@/app/api/jobs/search-tasks/[taskId]/route";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("job search task polling route", () => {
  it("forwards the capability in a header and never in the URL", async () => {
    vi.stubEnv("SOLARAHIRE_API_URL", "https://api.example.test/");
    const taskId = "20fe7844-bfdb-4a2e-ae32-13ae7426e969";
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({ task_id: taskId, status: "running" }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET(
      new Request(`http://localhost/api/jobs/search-tasks/${taskId}`, {
        headers: { "X-Task-Token": "opaque-capability-token" },
      }),
      { params: Promise.resolve({ taskId }) },
    );

    expect(response.status).toBe(200);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe(
      `https://api.example.test/api/v1/jobs/search-tasks/${taskId}`,
    );
    expect(url).not.toContain("opaque-capability-token");
    expect(new Headers(options.headers).get("X-Task-Token")).toBe(
      "opaque-capability-token",
    );
  });

  it("forwards cancellation without exposing the capability", async () => {
    vi.stubEnv("SOLARAHIRE_API_URL", "https://api.example.test/");
    const taskId = "20fe7844-bfdb-4a2e-ae32-13ae7426e969";
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({ task_id: taskId, status: "cancelled" }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await DELETE(
      new Request(`http://localhost/api/jobs/search-tasks/${taskId}`, {
        method: "DELETE",
        headers: { "X-Task-Token": "opaque-capability-token" },
      }),
      { params: Promise.resolve({ taskId }) },
    );

    expect(response.status).toBe(200);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe(
      `https://api.example.test/api/v1/jobs/search-tasks/${taskId}`,
    );
    expect(options.method).toBe("DELETE");
    expect(new Headers(options.headers).get("X-Task-Token")).toBe(
      "opaque-capability-token",
    );
  });
});
