// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/auth/session", () => ({
  resolveApiIdentity: vi.fn().mockResolvedValue({
    authorization: "Bearer server-only-token",
    sessionHeaders: new Headers(),
  }),
  attachSessionHeaders: (response: Response) => response,
}));

import { GET } from "@/app/api/reminders/route";

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("reminder collection route", () => {
  it("forwards the authenticated reminder list server-side", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(Response.json({ items: [] }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET(
      new Request("http://localhost/api/reminders"),
    );

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/reminders"),
      expect.objectContaining({ method: "GET" }),
    );
    const upstreamHeaders = fetchMock.mock.calls[0][1]?.headers as Headers;
    expect(upstreamHeaders.get("Authorization")).toBe(
      "Bearer server-only-token",
    );
  });
});
