import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteHeader } from "@/components/site-header";

const connection = {
  state: "online" as const,
  service: "Solara Hire",
  version: "1.0.0",
};

describe("SiteHeader", () => {
  it("offers secure sign-in and signup to anonymous visitors", () => {
    render(<SiteHeader connection={connection} user={null} />);

    expect(
      screen.getByRole("link", { name: "Solara Hire home" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute(
      "href",
      "/auth/login",
    );
    expect(
      screen.getByRole("link", { name: "Create account" }),
    ).toHaveAttribute("href", "/auth/login?screen_hint=signup");
  });

  it("shows a minimal account control without exposing tokens", () => {
    render(
      <SiteHeader
        connection={connection}
        user={{
          subject: "auth0|ada",
          name: "Ada Lovelace",
          email: "ada@example.com",
          emailVerified: true,
          picture: null,
        }}
      />,
    );

    expect(screen.getByText("Ada Lovelace")).toBeInTheDocument();
    expect(screen.getByText("ada@example.com")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Sign out" })).toHaveAttribute(
      "href",
      "/auth/logout",
    );
    expect(
      screen.queryByRole("link", { name: "Sign in" }),
    ).not.toBeInTheDocument();
  });
});
