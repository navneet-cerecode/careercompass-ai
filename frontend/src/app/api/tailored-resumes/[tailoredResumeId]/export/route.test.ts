// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/auth/session", () => ({
  resolveApiIdentity: vi.fn().mockResolvedValue({
    authorization: "Bearer server-only-token",
    sessionHeaders: new Headers(),
  }),
  attachSessionHeaders: (response: Response) => response,
}));

import { GET } from "@/app/api/tailored-resumes/[tailoredResumeId]/export/route";

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("tailored resume export route", () => {
  it("streams an authenticated document without exposing the access token", async () => {
    const bytes = new TextEncoder().encode("%PDF-private-resume");
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(bytes, {
        headers: {
          "Content-Type": "application/pdf",
          "Content-Disposition": 'attachment; filename="tailored-resume.pdf"',
        },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const id = "88cbb68a-6674-4601-b311-cf7645e0ad04";

    const response = await GET(
      new Request(`http://localhost/api/tailored-resumes/${id}/export?format=pdf`),
      { params: Promise.resolve({ tailoredResumeId: id }) },
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toBe("application/pdf");
    expect(response.headers.get("content-disposition")).toContain("tailored-resume.pdf");
    expect(new Uint8Array(await response.arrayBuffer())).toEqual(bytes);
    const headers = fetchMock.mock.calls[0][1]?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer server-only-token");
  });

  it("rejects unsupported formats before calling the backend", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const id = "88cbb68a-6674-4601-b311-cf7645e0ad04";

    const response = await GET(
      new Request(`http://localhost/api/tailored-resumes/${id}/export?format=html`),
      { params: Promise.resolve({ tailoredResumeId: id }) },
    );

    expect(response.status).toBe(400);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
