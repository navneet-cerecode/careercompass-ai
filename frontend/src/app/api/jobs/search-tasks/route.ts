import { forwardJsonRequest } from "@/lib/api/json-proxy";

export const runtime = "nodejs";

export async function POST(request: Request) {
  return forwardJsonRequest(request, {
    path: "/api/v1/jobs/search-tasks",
    timeoutMs: 10_000,
    maxBytes: 16 * 1024,
    serviceName: "job_search",
    forwardedHeaders: ["Idempotency-Key"],
  });
}
