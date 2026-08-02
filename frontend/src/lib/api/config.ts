const DEFAULT_API_URL = "http://127.0.0.1:8000";

export function getApiBaseUrl(
  environment: Readonly<Record<string, string | undefined>> = process.env,
): string {
  const configuredUrl =
    environment.SOLARAHIRE_API_URL?.trim() ??
    environment.CAREERCOMPASS_API_URL?.trim();
  const baseUrl = configuredUrl || DEFAULT_API_URL;

  let parsedUrl: URL;
  try {
    parsedUrl = new URL(baseUrl);
  } catch {
    throw new Error("SOLARAHIRE_API_URL must be an absolute HTTP(S) URL.");
  }

  if (!["http:", "https:"].includes(parsedUrl.protocol)) {
    throw new Error("SOLARAHIRE_API_URL must use HTTP or HTTPS.");
  }

  return parsedUrl.toString().replace(/\/$/, "");
}
