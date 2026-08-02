// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/auth/session", () => ({
  resolveApiIdentity: vi.fn().mockResolvedValue({
    authorization: "Bearer server-only-token",
    sessionHeaders: new Headers(),
  }),
  attachSessionHeaders: (response: Response) => response,
}));

import { PATCH } from "@/app/api/applications/[applicationId]/status/route";

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("application status route", () => {
  it("rejects malformed application identifiers before forwarding", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const response = await PATCH(
      new Request("http://localhost/api/applications/not-an-id/status", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "Applied" }),
      }),
      { params: Promise.resolve({ applicationId: "not-an-id" }) },
    );

    expect(response.status).toBe(404);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("forwards an allowed status request through the server boundary", async () => {
    const applicationId = "64d64589-c247-4df7-baf3-01c9fc10a39b";
    const fetchMock = vi
      .fn()
      .mockResolvedValue(Response.json({ id: applicationId }));
    vi.stubGlobal("fetch", fetchMock);
    const body = JSON.stringify({ status: "Ready to apply" });

    const response = await PATCH(
      new Request(
        `http://localhost/api/applications/${applicationId}/status`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body,
        },
      ),
      { params: Promise.resolve({ applicationId }) },
    );

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(`/api/v1/applications/${applicationId}/status`),
      expect.objectContaining({ method: "PATCH", body }),
    );
  });
});
