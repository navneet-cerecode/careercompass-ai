// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/auth/session", () => ({
  resolveApiIdentity: vi.fn().mockResolvedValue({
    authorization: "Bearer server-only-token",
    sessionHeaders: new Headers(),
  }),
  attachSessionHeaders: (response: Response) => response,
}));

import { POST } from "@/app/api/tailoring-plans/route";

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("tailoring plan route", () => {
  it("forwards an authenticated plan request without exposing the token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({ id: "factual-plan-id" }, { status: 201 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await POST(
      new Request("http://localhost/api/tailoring-plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: "job-id" }),
      }),
    );

    expect(response.status).toBe(201);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/tailoring-plans"),
      expect.objectContaining({ method: "POST" }),
    );
    const headers = fetchMock.mock.calls[0][1]?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer server-only-token");
  });
});
