import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RecommendationResults } from "@/components/recommendation-results";

const job = {
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
};

const results = {
  recommendations: [
    {
      id: "88cbb68a-6674-4601-b311-cf7645e0ad04",
      rank: 1,
      assessment: {
        id: "3285c75e-7b3c-4bdf-b8e3-099d0b6b0f90",
        job,
        score: 86,
        components: [],
        matched_skills: [],
        missing_skills: [],
        recruiter_summary: null,
        recommendations: [],
        confidence: 0.82,
        algorithm_version: "hybrid-v1",
      },
    },
  ],
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("RecommendationResults saved jobs", () => {
  it("saves a recommended role for a verified account", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(Response.json({ items: [] }))
      .mockResolvedValueOnce(
        Response.json({
          job,
          notes: null,
          created_at: "2026-08-02T10:00:00Z",
          updated_at: "2026-08-02T10:00:00Z",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(
      <RecommendationResults
        preferences={{
          role: "AI Engineer",
          location: "India",
          remoteOnly: false,
          employmentTypes: ["Full Time"],
          datePosted: "month",
        }}
        search={{
          status: "complete",
          jobs: [job],
          provider_failures: [],
          providers_attempted: 2,
          providers_succeeded: 2,
        }}
        results={results}
        onRefine={() => undefined}
        saveAccess="enabled"
      />,
    );

    await screen.findByRole("link", { name: /Saved roles/ });
    await user.click(screen.getByRole("button", { name: "Save AI Engineer" }));

    expect(
      await screen.findByText("AI Engineer is now in your saved roles."),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Remove AI Engineer" }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(fetchMock.mock.calls[1][0]).toBe(`/api/saved-jobs/${job.id}`);
  });

  it("offers secure sign-in without blocking anonymous recommendations", () => {
    render(
      <RecommendationResults
        preferences={{
          role: "AI Engineer",
          location: "India",
          remoteOnly: false,
          employmentTypes: ["Full Time"],
          datePosted: "month",
        }}
        search={{
          status: "complete",
          jobs: [job],
          provider_failures: [],
          providers_attempted: 2,
          providers_succeeded: 2,
        }}
        results={results}
        onRefine={() => undefined}
        saveAccess="sign-in"
      />,
    );

    expect(screen.getByRole("link", { name: /Sign in to save/ })).toHaveAttribute(
      "href",
      "/auth/login",
    );
    expect(screen.getByRole("heading", { name: "AI Engineer" })).toBeVisible();
  });
});
