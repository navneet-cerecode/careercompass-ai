import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ConnectionStatus } from "@/components/connection-status";

describe("ConnectionStatus", () => {
  it("announces a connected API version", () => {
    render(
      <ConnectionStatus
        connection={{
          state: "online",
          service: "CareerCompass AI",
          version: "1.0.0",
        }}
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent(
      "API connected · v1.0.0",
    );
  });

  it("keeps the frontend usable when the API is offline", () => {
    render(
      <ConnectionStatus
        connection={{ state: "offline", message: "API is unavailable." }}
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent(
      "Preview mode · API offline",
    );
  });
});
