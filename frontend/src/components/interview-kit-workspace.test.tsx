import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { InterviewKitWorkspace } from "@/components/interview-kit-workspace";
import type { ApplicationResponse, InterviewKitResponse } from "@/lib/api/job-contract";

const application = {
  id: "64d64589-c247-4df7-baf3-01c9fc10a39b",
  job: {
    id: "fa298c0d-23a4-4be0-aed2-93a41bf86ee2",
    title: "Operations Manager",
    company: "Northstar Foods",
    location: "Pune",
    description: "Lead reliable operations.",
    required_skills: [],
    experience_level: "Mid",
    employment_type: "Full Time",
    source: "Adzuna",
    source_name: "Adzuna",
    external_id: null,
    source_url: null,
    url: "https://example.com/jobs/operations-manager",
  },
  status: "Applied",
  allowed_next_statuses: ["Under review", "Assessment", "Interview", "Rejected", "Withdrawn"],
  packet_ready: true,
  resume_id: "f5763173-65cf-456c-8144-548921e42fcb",
  applied_at: "2026-08-02T10:00:00Z",
  notes: null,
  next_action: null,
  next_action_due_at: null,
  created_at: "2026-08-02T10:00:00Z",
  updated_at: "2026-08-02T10:00:00Z",
} as ApplicationResponse;

const kit = {
  id: "7f068b99-728d-4d1d-8fc4-304bed60fcc0",
  application_id: application.id,
  resume_id: application.resume_id,
  application_status: "Applied",
  job: application.job,
  questions: [
    {
      id: "career-story",
      category: "career_story",
      question: "How does your experience prepare you for this role?",
      why_it_matters: "Connect verified experience to the role.",
      evidence_prompts: ["Resume evidence: Improved daily operations."],
    },
  ],
  responses: {},
  reviewed_at: null,
  created_at: "2026-08-02T10:00:00Z",
  updated_at: "2026-08-02T10:00:00Z",
} as InterviewKitResponse;

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("InterviewKitWorkspace", () => {
  it("creates a factual preparation kit and saves user-authored notes", async () => {
    const user = userEvent.setup();
    const reviewed = {
      ...kit,
      responses: { "career-story": "I improved daily operations by 12%." },
      reviewed_at: "2026-08-09T10:00:00Z",
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(Response.json({ code: "interview_kit_not_found" }, { status: 404 }))
      .mockResolvedValueOnce(Response.json(kit, { status: 201 }))
      .mockResolvedValueOnce(Response.json(reviewed));
    vi.stubGlobal("fetch", fetchMock);

    render(<InterviewKitWorkspace application={application} />);
    await user.click(screen.getByRole("button", { name: "Prepare for interview" }));

    expect(await screen.findByText("Your interview evidence room")).toBeVisible();
    await user.click(screen.getByText("Resume evidence to consider"));
    expect(screen.getByText("Resume evidence: Improved daily operations.")).toBeVisible();
    await user.type(
      screen.getByLabelText("Your notes"),
      "I improved daily operations by 12%.",
    );
    await user.click(screen.getByRole("button", { name: "Save and mark fact-checked" }));

    expect(await screen.findByText("Reviewed by you")).toBeVisible();
    expect(fetchMock).toHaveBeenLastCalledWith(
      `/api/applications/${application.id}/interview-kit`,
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({
          responses: { "career-story": "I improved daily operations by 12%." },
          confirm_reviewed: true,
        }),
      }),
    );
  });
});
