import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { BillingWorkspace } from "@/components/billing-workspace";

const summary = {
  plan: "free",
  status: "active",
  provider: null,
  current_period_end: null,
  cancel_at_period_end: false,
  entitlements: {
    job_discovery: true,
    explainable_recommendations: true,
    tailored_documents: false,
    application_tracking: true,
    reminders: true,
  },
  checkout_available: false,
};

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("BillingWorkspace", () => {
  it("shows effective access without implying checkout exists", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(Response.json(summary)));
    render(<BillingWorkspace />);

    expect(await screen.findByRole("heading", { name: "Free" })).toBeInTheDocument();
    expect(screen.getByText("No payment method is required. Checkout is not available yet.")).toBeInTheDocument();
    expect(screen.getByText("Tailored documents")).toBeInTheDocument();
    expect(screen.getByText("Soon")).toBeInTheDocument();
  });

  it("recovers from a temporary error", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(Response.json({ message: "Please retry." }, { status: 503 }))
      .mockResolvedValueOnce(Response.json(summary));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<BillingWorkspace />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(await screen.findByRole("heading", { name: "Free" })).toBeInTheDocument();
  });
});
