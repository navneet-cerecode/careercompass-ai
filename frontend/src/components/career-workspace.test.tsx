import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CareerWorkspace } from "@/components/career-workspace";

const job = {
  id: "fa298c0d-23a4-4be0-aed2-93a41bf86ee2",
  title: "AI Engineer",
  company: "Analytical Engines",
  location: "Remote",
  description: "Build reliable AI systems.",
  required_skills: [{ name: "Python", category: "technical" }],
  experience_level: "Entry",
  employment_type: "Full Time",
  source: "JSearch",
  source_name: "JSearch",
  url: "https://example.com/jobs/ai-engineer",
};

const parsedProfile = {
  resume: {
    id: "d8a45758-b7b2-4896-bf85-48051b9c077e",
    name: "Ada Lovelace",
    email: "ada@example.com",
    phone: null,
    linkedin: null,
    github: null,
    education: [],
    experience: ["Built an analytical engine program"],
    projects: [],
    skills: [{ name: "Python", category: "technical" }],
    certifications: [],
    achievements: [],
  },
  raw_text: "Ada Lovelace\nPython engineer",
};

const searchResponse = {
  status: "partial",
  jobs: [job],
  provider_failures: [{ provider_name: "Adzuna", code: "provider_failed" }],
  providers_attempted: 4,
  providers_succeeded: 3,
};

const recommendationResponse = {
  recommendations: [
    {
      id: "88cbb68a-6674-4601-b311-cf7645e0ad04",
      rank: 1,
      assessment: {
        id: "3285c75e-7b3c-4bdf-b8e3-099d0b6b0f90",
        job,
        score: 86,
        components: [
          {
            name: "Skill evidence",
            score: 90,
            explanation: "Python appears in both the reviewed resume and role.",
            matched_skills: [{ name: "Python", category: "technical" }],
            missing_skills: [],
          },
        ],
        matched_skills: [{ name: "Python", category: "technical" }],
        missing_skills: [{ name: "MLOps", category: "technical" }],
        recruiter_summary: "Strong foundation for an early-career AI role.",
        recommendations: ["Show one deployed AI project before applying."],
        confidence: 0.82,
        algorithm_version: "hybrid-v1",
      },
    },
  ],
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("CareerWorkspace", () => {
  it("moves from factual resume review to explainable ranked jobs", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(Response.json(parsedProfile))
      .mockResolvedValueOnce(Response.json(searchResponse))
      .mockResolvedValueOnce(Response.json(recommendationResponse));
    vi.stubGlobal("fetch", fetchMock);
    render(<CareerWorkspace />);

    await user.upload(
      screen.getByLabelText("Browse files"),
      new File(["Ada Lovelace"], "ada.txt", { type: "text/plain" }),
    );
    await user.click(
      screen.getByRole("button", { name: /Build my profile/ }),
    );
    await screen.findByRole("heading", { name: "Review what we found." });
    await user.click(
      screen.getByRole("button", { name: /Set preferences/ }),
    );

    await user.click(
      screen.getByRole("button", { name: /Review profile/ }),
    );
    expect(
      screen.getByRole("heading", { name: "Ada Lovelace" }),
    ).toBeVisible();
    await user.click(
      screen.getByRole("button", { name: /Set preferences/ }),
    );

    await user.type(
      screen.getByLabelText(/Role or career lane/),
      "AI Engineer",
    );
    await user.click(
      screen.getByRole("button", { name: /Find and rank jobs/ }),
    );

    expect(
      await screen.findByRole("heading", {
        name: "Your clearest next moves.",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "AI Engineer" })).toBeVisible();
    expect(screen.getByText("MLOps")).toBeVisible();
    expect(
      screen.getByText("Results are ready, with partial provider coverage."),
    ).toBeVisible();
    expect(screen.getByRole("link", { name: /Review job/ })).toHaveAttribute(
      "href",
      "https://example.com/jobs/ai-engineer",
    );

    const recommendationRequest = JSON.parse(
      String(fetchMock.mock.calls[2][1]?.body),
    );
    expect(recommendationRequest.resume.raw_text).toBe(
      "Ada Lovelace\nPython engineer",
    );
    expect(recommendationRequest.job_ids).toEqual([job.id]);
  });

  it("offers recovery when verified search results are empty", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(Response.json(parsedProfile))
        .mockResolvedValueOnce(
          Response.json({
            status: "complete",
            jobs: [],
            provider_failures: [],
            providers_attempted: 4,
            providers_succeeded: 4,
          }),
        ),
    );
    render(<CareerWorkspace />);

    await user.upload(
      screen.getByLabelText("Browse files"),
      new File(["Ada"], "ada.txt", { type: "text/plain" }),
    );
    await user.click(
      screen.getByRole("button", { name: /Build my profile/ }),
    );
    await screen.findByRole("heading", { name: "Review what we found." });
    await user.click(
      screen.getByRole("button", { name: /Set preferences/ }),
    );
    await user.type(
      screen.getByLabelText(/Role or career lane/),
      "Astronaut",
    );
    await user.click(
      screen.getByRole("button", { name: /Find and rank jobs/ }),
    );

    expect(
      await screen.findByRole("heading", {
        name: "We could not finish this match set.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Refine preferences" }),
    ).toBeVisible();
  });
});
