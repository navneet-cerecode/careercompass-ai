import { forwardJsonRequest } from "@/lib/api/json-proxy";

export const runtime = "nodejs";

export async function POST(request: Request) {
  return forwardJsonRequest(request, {
    path: "/api/v1/jobs/search",
    timeoutMs: 45_000,
    maxBytes: 16 * 1024,
    serviceName: "job_search",
  });
}
