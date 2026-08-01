import { forwardJsonRequest } from "@/lib/api/json-proxy";

export const runtime = "nodejs";

export async function POST(request: Request) {
  return forwardJsonRequest(request, {
    path: "/api/v1/recommendations",
    timeoutMs: 60_000,
    maxBytes: 6 * 1024 * 1024,
    serviceName: "recommendations",
  });
}
