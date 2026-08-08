import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CoverLetterWorkspace } from "@/components/cover-letter-workspace";

const content = {
  candidate_name: "Avery Candidate",
  candidate_email: "avery@example.com",
  company_name: "Example Ltd",
  job_title: "Operations Manager",
  salutation: "Dear hiring team,",
  opening: "I am applying for the Operations Manager position at Example Ltd.",
  evidence_paragraph: "My verified background includes Excel.",
  motivation_paragraph: "A related project from my resume is: Stock forecast.",
  closing_paragraph: "Thank you for considering my application.",
  sign_off: "Sincerely,",
};

const draft = {
  id: "88cbb68a-6674-4601-b311-cf7645e0ad04",
  plan_id: "1738d8f6-6393-4ae1-bf8f-781f6b15aef6",
  source_resume_id: "3285c75e-7b3c-4bdf-b8e3-099d0b6b0f90",
  job_id: "fa298c0d-23a4-4be0-aed2-93a41bf86ee2",
  version: 1,
  suggested: content,
  accepted: content,
  evidence: [
    { kind: "skill" as const, source_index: 0, source_text: "Excel" },
    {
      kind: "experience" as const,
      source_index: 0,
      source_text: "Built weekly inventory reports in Excel.",
    },
  ],
  verification_status: "pending_review" as const,
  user_review_required: true,
  approved_at: null,
  created_at: "2026-08-08T10:00:00Z",
  updated_at: "2026-08-08T10:00:00Z",
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("CoverLetterWorkspace", () => {
  it("versions edits, exposes evidence, requires confirmation, and unlocks exports", async () => {
    const user = userEvent.setup();
    const revised = {
      ...draft,
      id: "b2634302-504d-44c4-88ea-e971cac12c06",
      version: 2,
      accepted: { ...content, opening: "I am applying for this position." },
    };
    const approved = {
      ...revised,
      verification_status: "user_verified" as const,
      user_review_required: false,
      approved_at: "2026-08-08T10:05:00Z",
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(Response.json(draft, { status: 201 }))
      .mockResolvedValueOnce(Response.json({ items: [draft] }))
      .mockResolvedValueOnce(Response.json(revised, { status: 201 }))
      .mockResolvedValueOnce(Response.json({ items: [revised, draft] }))
      .mockResolvedValueOnce(Response.json(approved))
      .mockResolvedValueOnce(Response.json({ items: [approved, draft] }));
    vi.stubGlobal("fetch", fetchMock);

    render(<CoverLetterWorkspace planId={draft.plan_id} jobTitle="Operations Manager" />);
    await user.click(screen.getByRole("button", { name: "Draft from verified evidence" }));

    expect(
      await screen.findByRole("region", { name: "Cover letter review for Operations Manager" }),
    ).toBeVisible();
    expect(screen.getByText("Built weekly inventory reports in Excel.")).toBeVisible();
    const opening = screen.getByLabelText("Opening");
    await user.clear(opening);
    await user.type(opening, "I am applying for this position.");
    expect(
      screen.getByRole("checkbox", { name: /confirm all candidate claims/ }),
    ).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "Save edits as new version" }));
    expect(await screen.findByText("Version 2 saved.", { exact: false })).toBeVisible();
    const confirmation = screen.getByRole("checkbox", {
      name: /confirm all candidate claims/,
    });
    await user.click(confirmation);
    await user.click(screen.getByRole("button", { name: "Confirm factual review" }));

    expect(await screen.findByText("PDF and DOCX exports are ready.", { exact: false })).toBeVisible();
    expect(screen.getByRole("link", { name: "Download PDF" })).toHaveAttribute(
      "href",
      `/api/cover-letters/${revised.id}/export?format=pdf`,
    );
    expect(screen.getByRole("link", { name: "Download DOCX" })).toHaveAttribute(
      "href",
      `/api/cover-letters/${revised.id}/export?format=docx`,
    );
    expect(screen.getByText("Version history (2)")).toBeVisible();
  });
});
