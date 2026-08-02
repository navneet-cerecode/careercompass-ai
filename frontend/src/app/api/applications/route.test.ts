// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/auth/session", () => ({
  resolveApiIdentity: vi.fn().mockResolvedValue({
    authorization: "Bearer server-only-token",
    sessionHeaders: new Headers(),
  }),
  attachSessionHeaders: (response: Response) => response,
}));

import { GET, POST } from "@/app/api/applications/route";

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("applications collection route", () => {
  it("forwards the authenticated list request server-side", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(Response.json({ items: [] }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET(
      new Request("http://localhost/api/applications"),
    );

    expect(response.status).toBe(200);
    const upstreamHeaders = fetchMock.mock.calls[0][1]?.headers as Headers;
    expect(upstreamHeaders.get("Authorization")).toBe(
      "Bearer server-only-token",
    );
  });

  it("validates and forwards create JSON without exposing the token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({ id: "64d64589-c247-4df7-baf3-01c9fc10a39b" }, {
        status: 201,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const body = JSON.stringify({
      job_id: "fa298c0d-23a4-4be0-aed2-93a41bf86ee2",
    });

    const response = await POST(
      new Request("http://localhost/api/applications", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
      }),
    );

    expect(response.status).toBe(201);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/applications"),
      expect.objectContaining({ method: "POST", body }),
    );
  });
});
