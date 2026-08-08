import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TailoringPlanAction } from "@/components/tailoring-plan-action";

const jobId = "fa298c0d-23a4-4be0-aed2-93a41bf86ee2";
const plan = {
  id: "88cbb68a-6674-4601-b311-cf7645e0ad04",
  source_resume_id: "3285c75e-7b3c-4bdf-b8e3-099d0b6b0f90",
  job_id: jobId,
  skills: [{ name: "Excel", category: null }],
  experience: ["Built weekly inventory reports in Excel."],
  projects: ["Forecasted stock requirements for a regional team."],
  matched_skills: [{ name: "Excel", category: null }],
  missing_skills: [{ name: "Inventory Planning", category: null }],
  evidence: [
    {
      section: "experience",
      source_index: 0,
      source_text: "Built weekly inventory reports in Excel.",
      matched_terms: ["Excel"],
    },
  ],
  user_review_required: true,
  algorithm_version: "factual-ordering-v1",
  created_at: "2026-08-08T10:00:00Z",
  updated_at: "2026-08-08T10:00:00Z",
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("TailoringPlanAction", () => {
  it("keeps anonymous users on a secure sign-in path", () => {
    render(
      <TailoringPlanAction
        jobId={jobId}
        jobTitle="Inventory Analyst"
        access="sign-in"
      />,
    );

    expect(screen.getByRole("link", { name: "Sign in to tailor" })).toHaveAttribute(
      "href",
      "/auth/login",
    );
  });

  it("shows reordered source evidence and keeps gaps separate", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn().mockResolvedValue(Response.json(plan, { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);
    render(
      <TailoringPlanAction
        jobId={jobId}
        jobTitle="Inventory Analyst"
        access="enabled"
      />,
    );

    await user.click(screen.getByRole("button", { name: "Tailor with my facts" }));

    expect(
      await screen.findByRole("region", {
        name: "Factual tailoring plan for Inventory Analyst",
      }),
    ).toBeVisible();
    expect(screen.getByText("Nothing new was written.", { exact: false })).toBeVisible();
    expect(screen.getByText("Inventory Planning")).toBeVisible();
    expect(
      screen.getAllByText("Built weekly inventory reports in Excel."),
    ).toHaveLength(2);
    expect(screen.getByText("Matches: Excel")).toBeVisible();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/tailoring-plans",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ job_id: jobId }),
      }),
    );
  });

  it("explains unavailable plan access without hiding the job", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        Response.json(
          {
            code: "tailored_documents_unavailable",
            message: "Your current plan does not include tailored documents.",
          },
          { status: 403 },
        ),
      ),
    );
    render(
      <TailoringPlanAction
        jobId={jobId}
        jobTitle="Inventory Analyst"
        access="enabled"
      />,
    );

    await user.click(screen.getByRole("button", { name: "Tailor with my facts" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Your current plan does not include tailored documents.",
    );
    expect(screen.getByRole("link", { name: "Review plan access" })).toHaveAttribute(
      "href",
      "/settings/billing",
    );
  });
});
