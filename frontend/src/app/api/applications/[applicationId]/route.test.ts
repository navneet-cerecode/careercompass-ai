// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/auth/session", () => ({
  resolveApiIdentity: vi.fn().mockResolvedValue({
    authorization: "Bearer server-only-token",
    sessionHeaders: new Headers(),
  }),
  attachSessionHeaders: (response: Response) => response,
}));

import {
  GET,
  PATCH,
} from "@/app/api/applications/[applicationId]/route";

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("application detail route", () => {
  it("forwards detail and planning requests through the server boundary", async () => {
    const applicationId = "64d64589-c247-4df7-baf3-01c9fc10a39b";
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(Response.json({ id: applicationId }))
      .mockResolvedValueOnce(Response.json({ id: applicationId }));
    vi.stubGlobal("fetch", fetchMock);

    const detail = await GET(
      new Request(`http://localhost/api/applications/${applicationId}`),
      { params: Promise.resolve({ applicationId }) },
    );
    expect(detail.status).toBe(200);

    const body = JSON.stringify({
      next_action: "Follow up",
      next_action_due_at: "2026-08-12T09:30:00Z",
    });
    const updated = await PATCH(
      new Request(`http://localhost/api/applications/${applicationId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body,
      }),
      { params: Promise.resolve({ applicationId }) },
    );

    expect(updated.status).toBe(200);
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringContaining(`/api/v1/applications/${applicationId}`),
      expect.objectContaining({ method: "PATCH", body }),
    );
  });

  it("rejects malformed identifiers before reading a request body", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const response = await PATCH(
      new Request("http://localhost/api/applications/not-an-id", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      }),
      { params: Promise.resolve({ applicationId: "not-an-id" }) },
    );

    expect(response.status).toBe(404);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
