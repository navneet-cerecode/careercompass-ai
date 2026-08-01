import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { CandidateProfileEditor } from "@/components/candidate-profile-editor";

const profile = {
  id: "a3877e65-a19c-496d-a73f-a64d29766468",
  name: "Ada Lovelace",
  email: "ada@example.com",
  phone: null,
  linkedin: null,
  github: "github.com/ada",
  education: ["BSc Mathematics"],
  experience: ["Built the Analytical Engine program"],
  projects: [],
  skills: [
    { name: "Python", category: "technical" },
    { name: "SQL", category: "technical" },
  ],
  certifications: [],
  achievements: [],
};

describe("CandidateProfileEditor", () => {
  it("requires a candidate name before saving", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    render(
      <CandidateProfileEditor
        profile={profile}
        onCancel={vi.fn()}
        onSave={onSave}
      />,
    );

    await user.clear(screen.getByLabelText("Name *"));
    await user.click(
      screen.getByRole("button", { name: /Save reviewed profile/ }),
    );

    expect(
      screen.getByText("Add your name before saving the reviewed profile."),
    ).toBeInTheDocument();
    expect(onSave).not.toHaveBeenCalled();
  });

  it("normalizes corrected fields without inventing profile data", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    render(
      <CandidateProfileEditor
        profile={profile}
        onCancel={vi.fn()}
        onSave={onSave}
      />,
    );

    await user.clear(screen.getByLabelText(/^Skills/));
    await user.type(
      screen.getByLabelText(/^Skills/),
      "Python, TypeScript, python",
    );
    await user.clear(screen.getByLabelText("Experience"));
    await user.type(
      screen.getByLabelText("Experience"),
      "Built the Analytical Engine program\nReviewed mathematical proofs",
    );
    await user.click(
      screen.getByRole("button", { name: /Save reviewed profile/ }),
    );

    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({
        id: profile.id,
        skills: [
          { name: "Python", category: "technical" },
          { name: "TypeScript", category: null },
        ],
        experience: [
          "Built the Analytical Engine program",
          "Reviewed mathematical proofs",
        ],
      }),
    );
  });

  it("allows the correction session to be cancelled", async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    render(
      <CandidateProfileEditor
        profile={profile}
        onCancel={onCancel}
        onSave={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onCancel).toHaveBeenCalledOnce();
  });
});
