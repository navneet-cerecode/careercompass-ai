// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/auth/session", () => ({
  resolveApiIdentity: vi.fn().mockResolvedValue({
    authorization: "Bearer server-only-token",
    sessionHeaders: new Headers(),
  }),
  attachSessionHeaders: (response: Response) => response,
}));

import { PATCH, POST } from "@/app/api/applications/[applicationId]/packet/route";

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("application packet route", () => {
  it("rejects malformed application identifiers before forwarding", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const response = await POST(
      new Request("http://localhost/api/applications/not-an-id/packet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      }),
      { params: Promise.resolve({ applicationId: "not-an-id" }) },
    );

    expect(response.status).toBe(404);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("forwards review changes through the authenticated server boundary", async () => {
    const applicationId = "64d64589-c247-4df7-baf3-01c9fc10a39b";
    const fetchMock = vi.fn().mockResolvedValue(Response.json({ application_id: applicationId }));
    vi.stubGlobal("fetch", fetchMock);
    const body = JSON.stringify({ resume_reviewed: true });

    const response = await PATCH(
      new Request(`http://localhost/api/applications/${applicationId}/packet`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body,
      }),
      { params: Promise.resolve({ applicationId }) },
    );

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(`/api/v1/applications/${applicationId}/packet`),
      expect.objectContaining({ method: "PATCH", body }),
    );
  });
});
