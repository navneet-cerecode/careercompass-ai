import { describe, expect, it } from "vitest";

import { getApiBaseUrl } from "@/lib/api/config";

describe("getApiBaseUrl", () => {
  it("uses a safe local default", () => {
    expect(getApiBaseUrl({})).toBe("http://127.0.0.1:8000");
  });

  it("normalizes an explicit server-only URL", () => {
    expect(
      getApiBaseUrl({
        CAREERCOMPASS_API_URL: "https://api.careercompass.example/",
      }),
    ).toBe("https://api.careercompass.example");
  });

  it("rejects non-HTTP schemes", () => {
    expect(() =>
      getApiBaseUrl({ CAREERCOMPASS_API_URL: "file:///tmp/secrets" }),
    ).toThrow("must use HTTP or HTTPS");
  });
});
