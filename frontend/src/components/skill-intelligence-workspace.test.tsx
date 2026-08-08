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
  skills: [
    {
      name: "Communication",
      category: "People",
      status: "supported",
      resume_evidenced: true,
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
      observed_role_count: 2,
      observed_roles: [],
    },
    {
      name: "Excel",
      category: "Tools",
      status: "resume_only",
      resume_evidenced: true,
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
    expect(screen.getByRole("row", { name: /Communication/ })).toBeVisible();
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
