import { describe, expect, it } from "vitest";

import {
  getApiErrorMessage,
  MAX_RESUME_BYTES,
  validateResumeFile,
} from "@/lib/api/resume-contract";

describe("resume contract helpers", () => {
  it("accepts supported resume files within the upload boundary", () => {
    const file = new File(["Ada Lovelace"], "resume.PDF", {
      type: "application/pdf",
    });

    expect(validateResumeFile(file)).toBeNull();
  });

  it("rejects unsupported, empty, and oversized files", () => {
    expect(validateResumeFile(new File(["resume"], "resume.rtf"))).toMatch(
      /PDF, DOCX, or plain-text/,
    );
    expect(validateResumeFile(new File([], "resume.txt"))).toMatch(/empty/);
    expect(
      validateResumeFile(
        new File([new Uint8Array(MAX_RESUME_BYTES + 1)], "resume.pdf"),
      ),
    ).toMatch(/5 MB or smaller/);
  });

  it("reads only a stable API error message", () => {
    expect(
      getApiErrorMessage({
        code: "invalid_resume",
        message: "The resume is invalid.",
      }),
    ).toBe("The resume is invalid.");
    expect(getApiErrorMessage({ message: 42 })).toBeNull();
    expect(getApiErrorMessage(null)).toBeNull();
  });
});
