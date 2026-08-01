// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

import { POST } from "@/app/api/recommendations/route";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("recommendation route", () => {
  it("preserves stable FastAPI recommendation failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        Response.json(
          {
            code: "recommendation_unavailable",
            message: "Job recommendations are temporarily unavailable.",
          },
          { status: 503 },
        ),
      ),
    );

    const response = await POST(
      new Request("http://localhost/api/recommendations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume: { name: "Ada", raw_text: "Ada resume" },
          job_ids: ["fa298c0d-23a4-4be0-aed2-93a41bf86ee2"],
        }),
      }),
    );

    expect(response.status).toBe(503);
    expect(await response.json()).toEqual({
      code: "recommendation_unavailable",
      message: "Job recommendations are temporarily unavailable.",
    });
  });

  it("returns a safe error when the recommendation service is offline", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    const response = await POST(
      new Request("http://localhost/api/recommendations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume: { name: "Ada", raw_text: "Ada resume" },
          job_ids: ["fa298c0d-23a4-4be0-aed2-93a41bf86ee2"],
        }),
      }),
    );

    expect(response.status).toBe(503);
    expect(await response.json()).toEqual({
      code: "recommendations_unavailable",
      message: "Recommendations are temporarily unavailable. Try again shortly.",
    });
  });
});
