import "server-only";

import type { components } from "@/lib/api/schema";
import { getApiBaseUrl } from "@/lib/api/config";

type HealthResponse = components["schemas"]["HealthResponse"];

export type ApiConnection =
  | {
      state: "online";
      service: string;
      version: string;
    }
  | {
      state: "offline";
      message: string;
    };

const HEALTH_TIMEOUT_MS = 2_500;

export async function getApiConnection(): Promise<ApiConnection> {
  try {
    const response = await fetch(`${getApiBaseUrl()}/api/v1/health/live`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS),
    });

    if (!response.ok) {
      return {
        state: "offline",
        message: `API health check returned ${response.status}.`,
      };
    }

    const health = (await response.json()) as HealthResponse;
    return {
      state: "online",
      service: health.service,
      version: health.version,
    };
  } catch {
    return {
      state: "offline",
      message: "API is not running locally.",
    };
  }
}
