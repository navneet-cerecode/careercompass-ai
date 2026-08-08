import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApplicationPacketWorkspace } from "@/components/application-packet-workspace";

const application = {
  id: "64d64589-c247-4df7-baf3-01c9fc10a39b",
  job: {
    id: "fa298c0d-23a4-4be0-aed2-93a41bf86ee2",
    title: "AI Engineer",
    company: "Analytical Engines",
    location: "Remote",
    description: "Build reliable AI systems.",
    required_skills: [],
    experience_level: "Entry" as const,
    employment_type: "Full Time" as const,
    source: "JSearch" as const,
    source_name: "JSearch",
    external_id: null,
    source_url: null,
    url: "https://example.com/jobs/ai-engineer",
  },
  status: "Preparing" as const,
  allowed_next_statuses: ["Withdrawn" as const],
  packet_ready: false,
  resume_id: "9254c329-b701-416e-bc81-1832366a7b0f",
  applied_at: null,
  notes: null,
  next_action: null,
  next_action_due_at: null,
  created_at: "2026-08-02T10:00:00Z",
  updated_at: "2026-08-02T10:00:00Z",
};

const packet = {
  id: "9d61516b-2b74-41ce-ae61-fc72f6db862d",
  application_id: application.id,
  source_resume_id: application.resume_id,
  tailored_resume_id: null,
  cover_letter_id: null,
  job_details_reviewed: false,
  resume_reviewed: false,
  cover_letter_reviewed: false,
  employer_questions_reviewed: false,
  ready_at: null,
  application_status: "Preparing" as const,
  blockers: [
    "job_details_not_reviewed",
    "resume_not_reviewed",
    "employer_questions_not_reviewed",
  ],
  can_mark_ready: false,
  can_confirm_submitted: false,
  available_tailored_resumes: [],
  available_cover_letters: [],
  created_at: "2026-08-02T10:00:00Z",
  updated_at: "2026-08-02T10:00:00Z",
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("ApplicationPacketWorkspace", () => {
  it("requires review, locks readiness, and records only confirmed external submission", async () => {
    const user = userEvent.setup();
    const reviewed = {
      ...packet,
      job_details_reviewed: true,
      resume_reviewed: true,
      employer_questions_reviewed: true,
      blockers: [],
      can_mark_ready: true,
    };
    const ready = {
      ...reviewed,
      ready_at: "2026-08-02T11:00:00Z",
      application_status: "Ready to apply" as const,
      can_mark_ready: false,
      can_confirm_submitted: true,
    };
    const submitted = {
      ...ready,
      application_status: "Applied" as const,
      can_confirm_submitted: false,
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(Response.json(packet, { status: 201 }))
      .mockResolvedValueOnce(Response.json(reviewed))
      .mockResolvedValueOnce(Response.json(ready))
      .mockResolvedValueOnce(Response.json(submitted));
    vi.stubGlobal("fetch", fetchMock);
    const changed = vi.fn().mockResolvedValue(undefined);

    render(
      <ApplicationPacketWorkspace
        application={application}
        onApplicationChanged={changed}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Build application packet" }));
    expect(await screen.findByText("3 checks left")).toBeVisible();
    expect(screen.queryByText(/auto-apply/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole("checkbox", { name: /I reviewed the role/i }));
    await user.click(screen.getByRole("checkbox", { name: /I reviewed the selected resume/i }));
    await user.click(
      screen.getByRole("checkbox", { name: /I reviewed the employer's application questions/i }),
    );
    await user.click(screen.getByRole("button", { name: "Save review" }));
    expect(await screen.findByText(/ready for your final confirmation/i)).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Mark packet ready" }));
    expect(await screen.findByRole("link", { name: /Continue on employer site/i })).toHaveAttribute(
      "href",
      application.job.url,
    );
    const recordButton = screen.getByRole("button", { name: "Record my submission" });
    expect(recordButton).toBeDisabled();
    await user.click(
      screen.getByRole("checkbox", { name: /I submitted this application/i }),
    );
    await user.click(recordButton);

    expect(await screen.findByText("Submission recorded from your confirmation.")).toBeVisible();
    expect(changed).toHaveBeenCalledTimes(2);
    expect(fetchMock).toHaveBeenNthCalledWith(
      4,
      `/api/applications/${application.id}/packet/submitted`,
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ confirm_external_submission: true }),
      }),
    );
  });
});
