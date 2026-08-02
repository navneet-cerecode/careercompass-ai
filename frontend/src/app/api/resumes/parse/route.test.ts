// @vitest-environment node

import { afterEach, describe, expect, it, vi } from "vitest";

import { POST } from "@/app/api/resumes/parse/route";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

function uploadRequest() {
  const formData = new FormData();
  formData.set(
    "file",
    new File(["Ada Lovelace"], "ada.txt", { type: "text/plain" }),
  );

  return new Request("http://localhost/api/resumes/parse", {
    method: "POST",
    body: formData,
  });
}

describe("resume parsing route", () => {
  it("rejects an oversized request before reading or forwarding it", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const response = await POST(
      new Request("http://localhost/api/resumes/parse", {
        method: "POST",
        headers: { "content-length": String(6 * 1024 * 1024) },
        body: new FormData(),
      }),
    );

    expect(response.status).toBe(413);
    expect(await response.json()).toEqual({
      code: "resume_too_large",
      message: "Your resume must be 5 MB or smaller.",
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("requires a file without calling the backend", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const response = await POST(
      new Request("http://localhost/api/resumes/parse", {
        method: "POST",
        body: new FormData(),
      }),
    );

    expect(response.status).toBe(400);
    expect(await response.json()).toEqual({
      code: "resume_required",
      message: "Choose a resume before continuing.",
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("forwards the upload and preserves typed backend failures", async () => {
    vi.stubEnv("SOLARAHIRE_API_URL", "https://api.example.test/");
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json(
        {
          code: "invalid_resume",
          message: "The uploaded text file contains binary data.",
        },
        { status: 422 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await POST(uploadRequest());

    expect(response.status).toBe(422);
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(await response.json()).toEqual({
      code: "invalid_resume",
      message: "The uploaded text file contains binary data.",
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.example.test/api/v1/resumes/parse",
      expect.objectContaining({
        method: "POST",
        cache: "no-store",
      }),
    );
  });

  it("returns a stable error when FastAPI is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    const response = await POST(uploadRequest());

    expect(response.status).toBe(503);
    expect(await response.json()).toEqual({
      code: "resume_service_unavailable",
      message: "Resume parsing is temporarily unavailable. Try again shortly.",
    });
  });
});
