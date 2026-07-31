import { getApiBaseUrl } from "@/lib/api/config";
import { MAX_RESUME_BYTES } from "@/lib/api/resume-contract";

export const runtime = "nodejs";

const RESUME_PARSE_TIMEOUT_MS = 30_000;
const MAX_MULTIPART_OVERHEAD_BYTES = 64 * 1024;

function errorResponse(status: number, code: string, message: string) {
  return Response.json(
    { code, message },
    {
      status,
      headers: { "Cache-Control": "no-store" },
    },
  );
}

export async function POST(request: Request) {
  const contentLength = Number(request.headers.get("content-length"));
  if (
    Number.isFinite(contentLength) &&
    contentLength > MAX_RESUME_BYTES + MAX_MULTIPART_OVERHEAD_BYTES
  ) {
    return errorResponse(
      413,
      "resume_too_large",
      "Your resume must be 5 MB or smaller.",
    );
  }

  let incomingForm: FormData;

  try {
    incomingForm = await request.formData();
  } catch {
    return errorResponse(
      400,
      "invalid_upload",
      "The resume upload could not be read.",
    );
  }

  const candidate = incomingForm.get("file");
  if (
    !candidate ||
    typeof candidate === "string" ||
    typeof candidate.name !== "string"
  ) {
    return errorResponse(
      400,
      "resume_required",
      "Choose a resume before continuing.",
    );
  }

  if (candidate.size > MAX_RESUME_BYTES) {
    return errorResponse(
      413,
      "resume_too_large",
      "Your resume must be 5 MB or smaller.",
    );
  }

  const upstreamForm = new FormData();
  upstreamForm.set("file", candidate, candidate.name);

  let upstreamResponse: Response;
  try {
    upstreamResponse = await fetch(
      `${getApiBaseUrl()}/api/v1/resumes/parse`,
      {
        method: "POST",
        body: upstreamForm,
        cache: "no-store",
        signal: AbortSignal.timeout(RESUME_PARSE_TIMEOUT_MS),
      },
    );
  } catch {
    return errorResponse(
      503,
      "resume_service_unavailable",
      "Resume parsing is temporarily unavailable. Try again shortly.",
    );
  }

  if (
    !upstreamResponse.headers
      .get("content-type")
      ?.toLowerCase()
      .includes("application/json")
  ) {
    return errorResponse(
      502,
      "invalid_resume_response",
      "The resume service returned an unexpected response.",
    );
  }

  try {
    const payload: unknown = await upstreamResponse.json();
    return Response.json(payload, {
      status: upstreamResponse.status,
      headers: { "Cache-Control": "no-store" },
    });
  } catch {
    return errorResponse(
      502,
      "invalid_resume_response",
      "The resume service returned an unexpected response.",
    );
  }
}
