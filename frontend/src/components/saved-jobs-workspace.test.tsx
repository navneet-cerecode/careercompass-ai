import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SavedJobsWorkspace } from "@/components/saved-jobs-workspace";

const savedJob = {
  job: {
    id: "fa298c0d-23a4-4be0-aed2-93a41bf86ee2",
    title: "AI Engineer",
    company: "Analytical Engines",
    location: "Remote",
    description: "Build reliable AI systems.",
    required_skills: [],
    experience_level: "Entry",
    employment_type: "Full Time",
    source: "JSearch",
    source_name: "JSearch",
    external_id: null,
    source_url: null,
    url: "https://example.com/jobs/ai-engineer",
  },
  notes: null,
  created_at: "2026-08-02T10:00:00Z",
  updated_at: "2026-08-02T10:00:00Z",
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("SavedJobsWorkspace", () => {
  it("loads and removes an account-owned saved role", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(Response.json({ items: [savedJob] }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<SavedJobsWorkspace />);

    expect(
      await screen.findByRole("heading", { name: "AI Engineer" }),
    ).toBeVisible();
    expect(screen.getByText("1 role")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Remove" }));

    expect(
      await screen.findByText("AI Engineer was removed from saved roles."),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Your shortlist has room." }),
    ).toBeVisible();
  });
});
