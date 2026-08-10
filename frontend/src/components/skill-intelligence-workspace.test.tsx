import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SkillIntelligenceWorkspace } from "@/components/skill-intelligence-workspace";

const snapshot = {
  resume_id: "f5763173-65cf-456c-8144-548921e42fcb",
  roles_analyzed: 4,
  roles_with_skill_data: 3,
  roles_without_skill_data: 1,
  search_history_roles: 3,
  saved_roles: 2,
  application_roles: 1,
  history_window: {
    first_observed_at: "2026-07-01T00:00:00Z",
    last_observed_at: "2026-08-09T00:00:00Z",
    observed_last_7_days: 2,
    observed_8_to_30_days: 1,
    observed_over_30_days: 1,
  },
  role_clusters: [
    {
      label: "Operations Manager",
      basis: "search_intent",
      role_count: 3,
      roles: [],
    },
    {
      label: "Supply Coordinator",
      basis: "role_title",
      role_count: 1,
      roles: [],
    },
  ],
  skills: [
    {
      name: "Communication",
      category: "People",
      status: "supported",
      resume_evidenced: true,
      match_confidence: "exact",
      matched_terms: ["Communication"],
      observed_role_count: 3,
      observed_roles: [
        {
          job_id: "fa298c0d-23a4-4be0-aed2-93a41bf86ee2",
          title: "Operations Manager",
          company: "Northstar Foods",
        },
      ],
    },
    {
      name: "Vendor Relations",
      category: "Operations",
      status: "develop",
      resume_evidenced: false,
      match_confidence: null,
      matched_terms: [],
      observed_role_count: 2,
      observed_roles: [],
    },
    {
      name: "MS Excel",
      category: "Tools",
      status: "supported",
      resume_evidenced: true,
      match_confidence: "curated_high",
      matched_terms: ["MS Excel", "Microsoft Excel"],
      observed_role_count: 1,
      observed_roles: [],
    },
    {
      name: "Bookkeeping",
      category: "Finance",
      status: "resume_only",
      resume_evidenced: true,
      match_confidence: null,
      matched_terms: [],
      observed_role_count: 0,
      observed_roles: [],
    },
  ],
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("SkillIntelligenceWorkspace", () => {
  it("labels the evidence boundary and filters the comparison matrix", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(Response.json(snapshot)));

    render(<SkillIntelligenceWorkspace />);

    expect(
      await screen.findByRole("heading", {
        name: "See what your chosen roles keep asking for.",
      }),
    ).toBeVisible();
    expect(screen.getByText(/not from the wider labor market/i)).toBeVisible();
    expect(screen.getByText("1 Jul 2026 – 9 Aug 2026")).toBeVisible();
    expect(screen.getByText(/not the employer’s posting date/i)).toBeVisible();
    expect(screen.getByText(/3 roles · Your search intent/i)).toBeVisible();
    expect(screen.getByText(/1 role · Exact role title/i)).toBeVisible();
    expect(screen.getByRole("row", { name: /Communication/ })).toBeVisible();
    expect(screen.getByText("Curated alias · high confidence")).toBeVisible();
    expect(screen.getByText("Matched terms: MS Excel ↔ Microsoft Excel")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Develop" }));
    expect(screen.getByRole("row", { name: /Vendor Relations/ })).toBeVisible();
    expect(screen.queryByRole("row", { name: /Communication/ })).not.toBeInTheDocument();
  });

  it("directs a user without a resume back to the reviewed upload flow", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        Response.json({
          ...snapshot,
          resume_id: null,
          roles_analyzed: 0,
          skills: [],
        }),
      ),
    );

    render(<SkillIntelligenceWorkspace />);

    expect(await screen.findByText("Start with a reviewed resume.")).toBeVisible();
    expect(screen.getByRole("link", { name: "Upload and review a resume" })).toHaveAttribute(
      "href",
      "/workspace",
    );
  });

  it("does not imply role demand when providers supplied no structured skills", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        Response.json({
          ...snapshot,
          roles_with_skill_data: 0,
          roles_without_skill_data: 4,
          skills: snapshot.skills.filter((skill) => skill.status === "resume_only"),
        }),
      ),
    );

    render(<SkillIntelligenceWorkspace />);

    expect(
      await screen.findByRole("heading", {
        name: "Your resume is ready. The role data is not—yet.",
      }),
    ).toBeVisible();
    expect(screen.getByText("Resume evidence inventory")).toBeVisible();
    expect(screen.queryByText(/roles keep asking/i)).not.toBeInTheDocument();
  });
});
