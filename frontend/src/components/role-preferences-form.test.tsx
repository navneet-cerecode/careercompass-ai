import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RolePreferencesForm } from "@/components/role-preferences-form";

const initialPreferences = {
  role: "",
  location: "India",
  country: "IN",
  remoteOnly: false,
  employmentTypes: ["Full Time" as const],
  datePosted: "month" as const,
};

describe("RolePreferencesForm", () => {
  it("requires a focused role before starting discovery", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(
      <RolePreferencesForm
        initialPreferences={initialPreferences}
        onBack={vi.fn()}
        onSubmit={onSubmit}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: /Find and rank jobs/ }),
    );

    expect(
      screen.getByText("Add the role or career lane you want to explore."),
    ).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("returns explicit filters selected by the user", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(
      <RolePreferencesForm
        initialPreferences={initialPreferences}
        onBack={vi.fn()}
        onSubmit={onSubmit}
      />,
    );

    await user.type(
      screen.getByLabelText(/Role or career lane/),
      "AI Engineer",
    );
    await user.click(screen.getByLabelText(/Remote roles only/));
    await user.click(screen.getByLabelText(/Contract/));
    await user.click(screen.getByLabelText("Past week"));
    await user.click(
      screen.getByRole("button", { name: /Find and rank jobs/ }),
    );

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        role: "AI Engineer",
        remoteOnly: true,
        employmentTypes: ["Full Time", "Contract"],
        datePosted: "week",
      }),
    );
  });
});
