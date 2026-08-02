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
  DELETE,
  PUT,
} from "@/app/api/saved-jobs/[jobId]/route";

const jobId = "fa298c0d-23a4-4be0-aed2-93a41bf86ee2";
const context = { params: Promise.resolve({ jobId }) };

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("saved job item route", () => {
  it("forwards an idempotent save request", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({
        job: { id: jobId },
        notes: null,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await PUT(
      new Request(`http://localhost/api/saved-jobs/${jobId}`, {
        method: "PUT",
        headers: {
          Cookie: "appSession=encrypted",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ notes: null }),
      }),
      context,
    );

    expect(response.status).toBe(200);
    expect(fetchMock.mock.calls[0][0]).toContain(
      `/api/v1/saved-jobs/${jobId}`,
    );
    expect(fetchMock.mock.calls[0][1]).toEqual(
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ notes: null }),
      }),
    );
  });

  it("preserves an empty successful delete response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 204 })),
    );

    const response = await DELETE(
      new Request(`http://localhost/api/saved-jobs/${jobId}`, {
        method: "DELETE",
        headers: { Cookie: "appSession=encrypted" },
      }),
      context,
    );

    expect(response.status).toBe(204);
    expect(await response.text()).toBe("");
  });

  it("rejects malformed job identifiers without calling FastAPI", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const response = await DELETE(
      new Request("http://localhost/api/saved-jobs/not-a-job", {
        method: "DELETE",
      }),
      { params: Promise.resolve({ jobId: "not-a-job" }) },
    );

    expect(response.status).toBe(404);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
