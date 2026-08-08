import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TailoredResumeWorkspace } from "@/components/tailored-resume-workspace";

const draft = {
  id: "88cbb68a-6674-4601-b311-cf7645e0ad04",
  plan_id: "1738d8f6-6393-4ae1-bf8f-781f6b15aef6",
  source_resume_id: "3285c75e-7b3c-4bdf-b8e3-099d0b6b0f90",
  job_id: "fa298c0d-23a4-4be0-aed2-93a41bf86ee2",
  version: 1,
  original: {
    name: "Avery Candidate",
    email: "avery@example.com",
    phone: null,
    linkedin: null,
    github: null,
    education: [],
    experience: ["Coordinated meetings.", "Built Excel reports."],
    projects: ["Created a stock forecast."],
    skills: [{ name: "Communication", category: null }, { name: "Excel", category: null }],
    certifications: [],
    achievements: [],
  },
  suggested: {
    name: "Avery Candidate",
    email: "avery@example.com",
    phone: null,
    linkedin: null,
    github: null,
    education: [],
    experience: ["Built Excel reports.", "Coordinated meetings."],
    projects: ["Created a stock forecast."],
    skills: [{ name: "Excel", category: null }, { name: "Communication", category: null }],
    certifications: [],
    achievements: [],
  },
  accepted: {
    name: "Avery Candidate",
    email: "avery@example.com",
    phone: null,
    linkedin: null,
    github: null,
    education: [],
    experience: ["Built Excel reports.", "Coordinated meetings."],
    projects: ["Created a stock forecast."],
    skills: [{ name: "Excel", category: null }, { name: "Communication", category: null }],
    certifications: [],
    achievements: [],
  },
  selections: { skills: "suggested", experience: "suggested", projects: "suggested" },
  verification_status: "pending_review" as const,
  user_review_required: true,
  approved_at: null,
  created_at: "2026-08-08T10:00:00Z",
  updated_at: "2026-08-08T10:00:00Z",
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("TailoredResumeWorkspace", () => {
  it("versions reviewed choices, requires confirmation, and exposes both exports", async () => {
    const user = userEvent.setup();
    const revised = {
      ...draft,
      id: "b2634302-504d-44c4-88ea-e971cac12c06",
      version: 2,
      selections: { ...draft.selections, experience: "original" as const },
      accepted: { ...draft.accepted, experience: draft.original.experience },
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

    render(
      <TailoredResumeWorkspace planId={draft.plan_id} jobTitle="Operations Manager" />,
    );
    await user.click(screen.getByRole("button", { name: "Compare and prepare export" }));

    expect(
      await screen.findByRole("region", { name: "Resume review for Operations Manager" }),
    ).toBeVisible();
    expect(screen.getByText("Original. Suggested. Your decision.")).toBeVisible();
    expect(screen.getByText("Accepted resume snapshot")).toBeVisible();
    expect(screen.getAllByText("Built Excel reports.")).toHaveLength(3);

    const originalChoices = screen.getAllByRole("radio", { name: /Original order/ });
    await user.click(originalChoices[1]);
    await user.click(screen.getByRole("button", { name: "Save choices as new version" }));

    expect(await screen.findByText("Version 2 saved.", { exact: false })).toBeVisible();
    const confirmation = screen.getByRole("checkbox", {
      name: /confirm it is factually accurate/,
    });
    await user.click(confirmation);
    await user.click(screen.getByRole("button", { name: "Confirm factual review" }));

    expect(
      await screen.findByText("PDF and DOCX exports are ready.", { exact: false }),
    ).toBeVisible();
    expect(screen.getByRole("link", { name: "Download PDF" })).toHaveAttribute(
      "href",
      `/api/tailored-resumes/${revised.id}/export?format=pdf`,
    );
    expect(screen.getByRole("link", { name: "Download DOCX" })).toHaveAttribute(
      "href",
      `/api/tailored-resumes/${revised.id}/export?format=docx`,
    );
    expect(screen.getByText("Version history (2)")).toBeVisible();
    expect(fetchMock.mock.calls[2][0]).toBe(
      `/api/tailored-resumes/${draft.id}/revisions`,
    );
    expect(fetchMock.mock.calls[4][0]).toBe(
      `/api/tailored-resumes/${revised.id}/approve`,
    );
  });
});
