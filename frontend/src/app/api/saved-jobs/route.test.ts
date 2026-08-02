// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/auth/session", () => ({
  resolveApiIdentity: vi.fn().mockResolvedValue({
    authorization: "Bearer server-only-token",
    sessionHeaders: new Headers(),
  }),
  attachSessionHeaders: (response: Response) => response,
}));

import { GET } from "@/app/api/saved-jobs/route";
import { resolveApiIdentity } from "@/lib/auth/session";

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("saved jobs collection route", () => {
  it("forwards identity only on the server", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({
        items: [],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET(
      new Request("http://localhost/api/saved-jobs", {
        headers: { Cookie: "appSession=encrypted" },
      }),
    );

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ items: [] });
    const upstreamHeaders = fetchMock.mock.calls[0][1]?.headers as Headers;
    expect(upstreamHeaders.get("Authorization")).toBe(
      "Bearer server-only-token",
    );
  });

  it("fails closed when no verified session exists", async () => {
    vi.mocked(resolveApiIdentity).mockResolvedValueOnce({
      authorization: null,
      sessionHeaders: new Headers(),
    });

    const response = await GET(
      new Request("http://localhost/api/saved-jobs"),
    );

    expect(response.status).toBe(401);
    expect(await response.json()).toEqual({
      code: "authentication_required",
      message: "Sign in to use account features.",
    });
  });
});
