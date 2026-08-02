import { forwardAuthenticatedRequest } from "@/lib/api/authenticated-proxy";

export const runtime = "nodejs";

export async function GET(request: Request) {
  return forwardAuthenticatedRequest(request, {
    path: "/api/v1/saved-jobs",
    method: "GET",
  });
}
