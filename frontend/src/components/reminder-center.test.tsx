import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ReminderCenter } from "@/components/reminder-center";

const reminder = {
  id: "64d64589-c247-4df7-baf3-01c9fc10a39b",
  application_id: "fa298c0d-23a4-4be0-aed2-93a41bf86ee2",
  job: {
    id: "93acb66d-96af-45f8-89f0-eb41798e8880",
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
  application_status: "Applied",
  next_action: "Follow up with the recruiter",
  due_at: "2026-08-12T09:30:00Z",
  status: "unread",
  read_at: null,
  dismissed_at: null,
  created_at: "2026-08-02T10:00:00Z",
  updated_at: "2026-08-02T10:00:00Z",
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ReminderCenter", () => {
  it("shows unread reminders and links to their application", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(Response.json({ items: [reminder] })),
    );

    render(<ReminderCenter />);

    const trigger = await screen.findByRole("button", {
      name: "Application reminders, 1 unread",
    });
    await user.click(trigger);
    expect(screen.getByText("Follow up with the recruiter")).toBeVisible();
    expect(
      screen.getByRole("link", { name: "Review application" }),
    ).toHaveAttribute(
      "href",
      `/applications#application-${reminder.application_id}`,
    );
    expect(
      screen.getByText(
        "Based only on deadlines you set · No employer status inferred",
      ),
    ).toBeVisible();
  });

  it("marks a reminder read without hiding it", async () => {
    const user = userEvent.setup();
    const readReminder = {
      ...reminder,
      status: "read",
      read_at: "2026-08-02T11:00:00Z",
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(Response.json({ items: [reminder] }))
      .mockResolvedValueOnce(Response.json(readReminder));
    vi.stubGlobal("fetch", fetchMock);

    render(<ReminderCenter />);
    await user.click(
      await screen.findByRole("button", {
        name: "Application reminders, 1 unread",
      }),
    );
    await user.click(screen.getByRole("button", { name: "Mark read" }));

    expect(
      await screen.findByRole("button", { name: "Application reminders" }),
    ).toBeVisible();
    expect(screen.getByText("Follow up with the recruiter")).toBeVisible();
  });

  it("dismisses a reminder from the active panel", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(Response.json({ items: [reminder] }))
      .mockResolvedValueOnce(
        Response.json({ ...reminder, status: "dismissed" }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<ReminderCenter />);
    await user.click(
      await screen.findByRole("button", {
        name: "Application reminders, 1 unread",
      }),
    );
    await user.click(screen.getByRole("button", { name: "Dismiss" }));

    expect(await screen.findByText("You are caught up.")).toBeVisible();
    expect(screen.queryByText("Follow up with the recruiter")).not.toBeInTheDocument();
  });

  it("closes the panel with Escape", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(Response.json({ items: [] })),
    );

    render(<ReminderCenter />);
    const trigger = await screen.findByRole("button", {
      name: "Application reminders",
    });
    await user.click(trigger);
    expect(
      screen.getByRole("region", { name: "Application reminders" }),
    ).toBeVisible();

    await user.keyboard("{Escape}");

    expect(
      screen.queryByRole("region", { name: "Application reminders" }),
    ).not.toBeInTheDocument();
    expect(trigger).toHaveAttribute("aria-expanded", "false");
  });
});
