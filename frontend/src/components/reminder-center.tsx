"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import type {
  ApplicationReminderListResponse,
  ApplicationReminderResponse,
  ApplicationReminderStatus,
  UpdateApplicationReminderRequest,
} from "@/lib/api/job-contract";
import { getApiErrorMessage } from "@/lib/api/resume-contract";

type ReminderState =
  | { status: "loading"; items: ApplicationReminderResponse[] }
  | { status: "error"; items: ApplicationReminderResponse[]; message: string }
  | { status: "ready"; items: ApplicationReminderResponse[] };

function isReminderList(value: unknown): value is ApplicationReminderListResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "items" in value &&
    Array.isArray(value.items)
  );
}

function isReminder(value: unknown): value is ApplicationReminderResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof value.id === "string" &&
    "status" in value
  );
}

function deadlineCopy(value: string) {
  const dueAt = new Date(value);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const dueDay = new Date(
    dueAt.getFullYear(),
    dueAt.getMonth(),
    dueAt.getDate(),
  );
  const dayDifference = Math.round(
    (dueDay.getTime() - today.getTime()) / 86_400_000,
  );
  const time = new Intl.DateTimeFormat("en", {
    hour: "numeric",
    minute: "2-digit",
  }).format(dueAt);

  if (dueAt.getTime() < now.getTime()) {
    return {
      tone: "overdue" as const,
      label: `Overdue · ${new Intl.DateTimeFormat("en", {
        day: "numeric",
        month: "short",
      }).format(dueAt)} at ${time}`,
    };
  }
  if (dayDifference === 0) {
    return { tone: "today" as const, label: `Today at ${time}` };
  }
  if (dayDifference === 1) {
    return { tone: "upcoming" as const, label: `Tomorrow at ${time}` };
  }
  return {
    tone: "upcoming" as const,
    label: new Intl.DateTimeFormat("en", {
      weekday: "short",
      day: "numeric",
      month: "short",
      hour: "numeric",
      minute: "2-digit",
    }).format(dueAt),
  };
}

export function ReminderCenter() {
  const [state, setState] = useState<ReminderState>({
    status: "loading",
    items: [],
  });
  const [open, setOpen] = useState(false);
  const [updating, setUpdating] = useState<Set<string>>(new Set());
  const rootRef = useRef<HTMLDivElement>(null);

  const loadReminders = useCallback(async () => {
    try {
      const response = await fetch("/api/reminders", { cache: "no-store" });
      const payload: unknown = await response.json();
      if (!response.ok || !isReminderList(payload)) {
        throw new Error(
          getApiErrorMessage(payload) ??
            "Solara Hire could not load your reminders.",
        );
      }
      setState({ status: "ready", items: [...payload.items] });
    } catch (error) {
      setState((current) => ({
        status: "error",
        items: current.items,
        message:
          error instanceof Error
            ? error.message
            : "Solara Hire could not load your reminders.",
      }));
    }
  }, []);

  useEffect(() => {
    void loadReminders();
    const refresh = () => void loadReminders();
    const intervalId = window.setInterval(refresh, 60_000);
    window.addEventListener("focus", refresh);
    window.addEventListener("solarahire:application-plan-updated", refresh);
    return () => {
      window.clearInterval(intervalId);
      window.removeEventListener("focus", refresh);
      window.removeEventListener("solarahire:application-plan-updated", refresh);
    };
  }, [loadReminders]);

  useEffect(() => {
    if (!open) return;
    const closeOnPointerDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", closeOnPointerDown);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOnPointerDown);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  const updateStatus = async (
    reminder: ApplicationReminderResponse,
    status: ApplicationReminderStatus,
  ) => {
    const request: UpdateApplicationReminderRequest = { status };
    setUpdating((current) => new Set(current).add(reminder.id));
    try {
      const response = await fetch(`/api/reminders/${reminder.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });
      const payload: unknown = await response.json();
      if (!response.ok || !isReminder(payload)) {
        throw new Error(
          getApiErrorMessage(payload) ??
            "Solara Hire could not update this reminder.",
        );
      }
      setState((current) => ({
        status: "ready",
        items:
          status === "dismissed"
            ? current.items.filter((item) => item.id !== reminder.id)
            : current.items.map((item) =>
                item.id === reminder.id ? payload : item,
              ),
      }));
    } catch (error) {
      setState((current) => ({
        status: "error",
        items: current.items,
        message:
          error instanceof Error
            ? error.message
            : "Solara Hire could not update this reminder.",
      }));
    } finally {
      setUpdating((current) => {
        const next = new Set(current);
        next.delete(reminder.id);
        return next;
      });
    }
  };

  const unreadCount = state.items.filter(
    (item) => item.status === "unread",
  ).length;

  return (
    <div className="reminder-center" ref={rootRef}>
      <button
        type="button"
        className="reminder-trigger"
        aria-expanded={open}
        aria-controls="application-reminder-panel"
        aria-label={`Application reminders${unreadCount ? `, ${unreadCount} unread` : ""}`}
        onClick={() => setOpen((current) => !current)}
      >
        <span className="reminder-bell" aria-hidden="true" />
        {unreadCount > 0 && (
          <span className="reminder-count" aria-hidden="true">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <section
          id="application-reminder-panel"
          className="reminder-panel"
          aria-label="Application reminders"
        >
          <div className="reminder-panel-heading">
            <div>
              <span>Application desk</span>
              <h2>Your next moves</h2>
            </div>
            <Link href="/applications" onClick={() => setOpen(false)}>
              Open tracker
            </Link>
          </div>

          {state.status === "loading" && state.items.length === 0 && (
            <div className="reminder-panel-state" aria-busy="true">
              <span aria-hidden="true" />
              <p>Checking your deadlines…</p>
            </div>
          )}

          {state.status === "error" && state.items.length === 0 && (
            <div className="reminder-panel-state is-error">
              <strong>Reminders are temporarily unavailable.</strong>
              <p>{state.message}</p>
              <button type="button" onClick={() => void loadReminders()}>
                Try again
              </button>
            </div>
          )}

          {state.status === "ready" && state.items.length === 0 && (
            <div className="reminder-panel-empty">
              <span aria-hidden="true">✓</span>
              <strong>You are caught up.</strong>
              <p>
                Add a next action and deadline in your tracker. Solara Hire will
                keep it in view.
              </p>
            </div>
          )}

          {state.items.length > 0 && (
            <div className="reminder-list">
              {state.items.map((reminder) => {
                const deadline = deadlineCopy(reminder.due_at);
                const busy = updating.has(reminder.id);
                return (
                  <article
                    className="reminder-item"
                    data-status={reminder.status}
                    key={reminder.id}
                  >
                    <div className="reminder-item-topline">
                      <span data-tone={deadline.tone}>{deadline.label}</span>
                      {reminder.status === "unread" && <i>New</i>}
                    </div>
                    <strong>{reminder.next_action}</strong>
                    <p>
                      {reminder.job.title} · {reminder.job.company}
                    </p>
                    <div className="reminder-item-actions">
                      <Link
                        href={`/applications#application-${reminder.application_id}`}
                        onClick={() => setOpen(false)}
                      >
                        Review application
                      </Link>
                      {reminder.status === "unread" && (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => void updateStatus(reminder, "read")}
                        >
                          Mark read
                        </button>
                      )}
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() =>
                          void updateStatus(reminder, "dismissed")
                        }
                      >
                        Dismiss
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          )}

          {state.status === "error" && state.items.length > 0 && (
            <p className="reminder-inline-error" role="status">
              {state.message}
            </p>
          )}

          <p className="reminder-provenance">
            Based only on deadlines you set · No employer status inferred
          </p>
        </section>
      )}
    </div>
  );
}
