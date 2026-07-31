import type { components } from "@/lib/api/schema";

export type ParsedResumeResponse =
  components["schemas"]["ParsedResumeResponse"];

export const MAX_RESUME_BYTES = 5 * 1024 * 1024;
export const ACCEPTED_RESUME_EXTENSIONS = [".pdf", ".docx", ".txt"] as const;

export function validateResumeFile(file: File): string | null {
  const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();

  if (
    !ACCEPTED_RESUME_EXTENSIONS.includes(
      extension as (typeof ACCEPTED_RESUME_EXTENSIONS)[number],
    )
  ) {
    return "Choose a PDF, DOCX, or plain-text resume.";
  }

  if (file.size === 0) {
    return "This file is empty. Choose a resume with content.";
  }

  if (file.size > MAX_RESUME_BYTES) {
    return "Your resume must be 5 MB or smaller.";
  }

  return null;
}

export function getApiErrorMessage(payload: unknown): string | null {
  if (
    typeof payload === "object" &&
    payload !== null &&
    "message" in payload &&
    typeof payload.message === "string"
  ) {
    return payload.message;
  }

  return null;
}
