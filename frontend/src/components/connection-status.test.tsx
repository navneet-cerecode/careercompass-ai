import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ConnectionStatus } from "@/components/connection-status";

describe("ConnectionStatus", () => {
  it("announces a connected API version", () => {
    render(
      <ConnectionStatus
        connection={{
          state: "online",
          service: "Solara Hire",
          version: "1.0.0",
        }}
      />,
    );

    const status = screen.getByRole("status");
    expect(status).toHaveAttribute("aria-label", "API connected · v1.0.0");
    expect(status).toHaveTextContent("API connected · v1.0.0");
    expect(status).toHaveTextContent("API online");
  });

  it("keeps the frontend usable when the API is offline", () => {
    render(
      <ConnectionStatus
        connection={{ state: "offline", message: "API is unavailable." }}
      />,
    );

    const status = screen.getByRole("status");
    expect(status).toHaveAttribute(
      "aria-label",
      "Preview mode · API offline",
    );
    expect(status).toHaveTextContent("API offline");
  });
});
