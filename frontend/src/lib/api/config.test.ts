import { describe, expect, it } from "vitest";

import { getApiBaseUrl } from "@/lib/api/config";

describe("getApiBaseUrl", () => {
  it("uses a safe local default", () => {
    expect(getApiBaseUrl({})).toBe("http://127.0.0.1:8000");
  });

  it("normalizes an explicit server-only URL", () => {
    expect(
      getApiBaseUrl({
        SOLARAHIRE_API_URL: "https://api.solarahire.example/",
      }),
    ).toBe("https://api.solarahire.example");
  });

  it("keeps the previous environment name as a migration fallback", () => {
    expect(
      getApiBaseUrl({
        CAREERCOMPASS_API_URL: "https://legacy-api.example/",
      }),
    ).toBe("https://legacy-api.example");
  });

  it("rejects non-HTTP schemes", () => {
    expect(() =>
      getApiBaseUrl({ SOLARAHIRE_API_URL: "file:///tmp/secrets" }),
    ).toThrow("must use HTTP or HTTPS");
  });
});
