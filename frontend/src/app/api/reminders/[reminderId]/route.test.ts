// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/auth/session", () => ({
  resolveApiIdentity: vi.fn().mockResolvedValue({
    authorization: "Bearer server-only-token",
    sessionHeaders: new Headers(),
  }),
  attachSessionHeaders: (response: Response) => response,
}));

import { PATCH } from "@/app/api/reminders/[reminderId]/route";

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("reminder detail route", () => {
  it("forwards a bounded state update through the authenticated boundary", async () => {
    const reminderId = "64d64589-c247-4df7-baf3-01c9fc10a39b";
    const fetchMock = vi
      .fn()
      .mockResolvedValue(Response.json({ id: reminderId, status: "read" }));
    vi.stubGlobal("fetch", fetchMock);
    const body = JSON.stringify({ status: "read" });

    const response = await PATCH(
      new Request(`http://localhost/api/reminders/${reminderId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body,
      }),
      { params: Promise.resolve({ reminderId }) },
    );

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(`/api/v1/reminders/${reminderId}`),
      expect.objectContaining({ method: "PATCH", body }),
    );
  });

  it("rejects malformed reminder identifiers locally", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const response = await PATCH(
      new Request("http://localhost/api/reminders/not-an-id", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      }),
      { params: Promise.resolve({ reminderId: "not-an-id" }) },
    );

    expect(response.status).toBe(404);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
