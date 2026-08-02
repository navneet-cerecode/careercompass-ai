// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

import { POST } from "@/app/api/jobs/search/route";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("job search route", () => {
  it("rejects non-JSON requests before forwarding", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const response = await POST(
      new Request("http://localhost/api/jobs/search", {
        method: "POST",
        body: "role=AI+Engineer",
      }),
    );

    expect(response.status).toBe(415);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("forwards search JSON only to the fixed FastAPI endpoint", async () => {
    vi.stubEnv("SOLARAHIRE_API_URL", "https://api.example.test/");
    const payload = {
      status: "complete",
      jobs: [],
      provider_failures: [],
      providers_attempted: 4,
      providers_succeeded: 4,
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValue(Response.json(payload, { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const body = JSON.stringify({
      role: "AI Engineer",
      location: "India",
      page: 1,
      page_size: 20,
      employment_types: ["Full Time"],
      date_posted: "month",
    });
    const response = await POST(
      new Request("http://localhost/api/jobs/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
      }),
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(await response.json()).toEqual(payload);
    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.example.test/api/v1/jobs/search",
      expect.objectContaining({
        method: "POST",
        body,
        cache: "no-store",
      }),
    );
  });
});
