import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApplicationTrackerWorkspace } from "@/components/application-tracker-workspace";

const application = {
  id: "64d64589-c247-4df7-baf3-01c9fc10a39b",
  job: {
    id: "fa298c0d-23a4-4be0-aed2-93a41bf86ee2",
    title: "AI Engineer",
    company: "Analytical Engines",
    location: "Remote",
    description: "Build reliable AI systems.",
    required_skills: [],
    experience_level: "Entry",
    employment_type: "Full Time",
    source: "JSearch",
    source_name: "JSearch",
    external_id: null,
    source_url: null,
    url: "https://example.com/jobs/ai-engineer",
  },
  status: "Preparing",
  allowed_next_statuses: ["Withdrawn"],
  packet_ready: false,
  resume_id: null,
  applied_at: null,
  notes: null,
  next_action: "Review the role",
  next_action_due_at: null,
  created_at: "2026-08-02T10:00:00Z",
  updated_at: "2026-08-02T10:00:00Z",
};

const detail = {
  ...application,
  events: [
    {
      id: "a8452d33-e0cf-4dd7-a526-6228a27f5a67",
      previous_status: null,
      new_status: "Preparing",
      note: "Created",
      occurred_at: "2026-08-02T10:00:00Z",
    },
  ],
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  window.history.replaceState({}, "", "/");
});

describe("ApplicationTrackerWorkspace", () => {
  it("renders an intentional empty state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(Response.json({ items: [] })),
    );

    render(<ApplicationTrackerWorkspace />);

    expect(
      await screen.findByRole("heading", {
        name: "Your next application starts with a role worth pursuing.",
      }),
    ).toBeVisible();
    expect(
      screen.getByRole("link", { name: "Review saved roles" }),
    ).toHaveAttribute("href", "/saved");
  });

  it("loads history and records only an allowed transition", async () => {
    const user = userEvent.setup();
    const transitioned = {
      ...detail,
      status: "Withdrawn",
      allowed_next_statuses: [],
      events: [
        ...detail.events,
        {
          id: "5ddfb7fa-1156-4fe1-9d82-90341d49ab45",
          previous_status: "Preparing",
          new_status: "Withdrawn",
          note: "Role is no longer a fit",
          occurred_at: "2026-08-02T11:00:00Z",
        },
      ],
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(Response.json({ items: [application] }))
      .mockResolvedValueOnce(Response.json(detail))
      .mockResolvedValueOnce(Response.json(transitioned));
    vi.stubGlobal("fetch", fetchMock);

    render(<ApplicationTrackerWorkspace />);

    await user.click(
      await screen.findByRole("button", { name: "History & next step" }),
    );
    expect(await screen.findByText("Started at Preparing")).toBeVisible();
    await user.type(
      screen.getByLabelText("What changed?"),
      "Role is no longer a fit",
    );
    await user.click(
      screen.getByRole("button", { name: "Confirm transition" }),
    );

    expect(
      await screen.findByText(
        "AI Engineer moved to Withdrawn. The change is in your history.",
      ),
    ).toBeVisible();
    expect(fetchMock).toHaveBeenLastCalledWith(
      `/api/applications/${application.id}/status`,
      expect.objectContaining({ method: "PATCH" }),
    );
  });

  it("updates planning fields without changing employer status", async () => {
    const user = userEvent.setup();
    const planned = {
      ...detail,
      notes: "Recruiter context",
      next_action: "Follow up with the recruiter",
      next_action_due_at: "2026-08-12T09:30:00Z",
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(Response.json({ items: [application] }))
      .mockResolvedValueOnce(Response.json(detail))
      .mockResolvedValueOnce(Response.json(planned));
    vi.stubGlobal("fetch", fetchMock);

    render(<ApplicationTrackerWorkspace />);

    await user.click(
      await screen.findByRole("button", { name: "History & next step" }),
    );
    await user.clear(await screen.findByLabelText("Next action"));
    await user.type(
      screen.getByLabelText("Next action"),
      "Follow up with the recruiter",
    );
    fireEvent.change(screen.getByLabelText("Deadline"), {
      target: { value: "2026-08-12T09:30" },
    });
    await user.type(screen.getByLabelText("Private notes"), "Recruiter context");
    await user.click(screen.getByRole("button", { name: "Save plan" }));

    expect(
      await screen.findByText(
        "AI Engineer planning details were updated. Its employer-status history is unchanged.",
      ),
    ).toBeVisible();
    expect(fetchMock).toHaveBeenLastCalledWith(
      `/api/applications/${application.id}`,
      expect.objectContaining({ method: "PATCH" }),
    );
  });

  it("focuses an application reached from a reminder deep link", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(Response.json({ items: [application] })),
    );
    const scrollIntoView = vi.fn();
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
      configurable: true,
      value: scrollIntoView,
    });
    window.history.replaceState(
      {},
      "",
      `/#application-${application.id}`,
    );

    render(<ApplicationTrackerWorkspace />);

    const heading = await screen.findByRole("heading", {
      name: "AI Engineer",
    });
    const card = heading.closest("article");
    await waitFor(() => expect(document.activeElement).toBe(card));
    expect(scrollIntoView).toHaveBeenCalledWith({ block: "center" });
  });
});
