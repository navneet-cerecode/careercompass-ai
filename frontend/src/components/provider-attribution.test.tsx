import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProviderAttribution } from "@/components/provider-attribution";

describe("ProviderAttribution", () => {
  it("links Muse attribution back to the original Muse listing", () => {
    render(
      <ProviderAttribution
        source="The Muse"
        source_name="the_muse"
        source_url="https://www.themuse.com/jobs/northstar/operations-manager"
      />,
    );

    expect(screen.getByRole("link", { name: "The Muse" })).toHaveAttribute(
      "href",
      "https://www.themuse.com/jobs/northstar/operations-manager",
    );
  });
});
