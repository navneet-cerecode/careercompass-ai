// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/auth/session", () => ({
  resolveApiIdentity: vi.fn().mockResolvedValue({
    authorization: "Bearer server-only-token",
    sessionHeaders: new Headers(),
  }),
  attachSessionHeaders: (response: Response) => response,
}));

import { GET } from "@/app/api/skill-intelligence/route";

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("skill intelligence route", () => {
  it("forwards only through the authenticated server boundary", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({ roles_analyzed: 0, skills: [] }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET(
      new Request("http://localhost/api/skill-intelligence", {
        headers: { cookie: "appSession=opaque" },
      }),
    );

    expect(response.status).toBe(200);
    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/skill-intelligence");
    expect(fetchMock.mock.calls[0][1]?.method).toBe("GET");
    const upstreamHeaders = fetchMock.mock.calls[0][1]?.headers as Headers;
    expect(upstreamHeaders.get("Authorization")).toBe("Bearer server-only-token");
  });
});
