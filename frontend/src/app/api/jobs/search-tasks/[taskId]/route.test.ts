// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

import { GET } from "@/app/api/jobs/search-tasks/[taskId]/route";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("job search task polling route", () => {
  it("forwards the capability in a header and never in the URL", async () => {
    vi.stubEnv("CAREERCOMPASS_API_URL", "https://api.example.test/");
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
    expect(options.headers["X-Task-Token"]).toBe("opaque-capability-token");
  });
});
