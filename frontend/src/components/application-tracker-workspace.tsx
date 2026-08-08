"use client";

import {
  useEffect,
  useState,
  type FormEvent,
} from "react";

import { ProviderAttribution } from "@/components/provider-attribution";
import type {
  ApplicationDetailResponse,
  ApplicationListResponse,
  ApplicationResponse,
  ApplicationStatus,
  TransitionApplicationRequest,
  UpdateApplicationPlanRequest,
} from "@/lib/api/job-contract";
import { getApiErrorMessage } from "@/lib/api/resume-contract";

type TrackerState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; items: ApplicationResponse[] };

type TrackerGroup = {
  id: "preparing" | "active" | "outcomes";
  eyebrow: string;
  title: string;
  statuses: ApplicationStatus[];
};

const TRACKER_GROUPS: TrackerGroup[] = [
  {
    id: "preparing",
    eyebrow: "Build the case",
    title: "Preparing",
    statuses: ["Discovered", "Saved", "Preparing", "Ready to apply"],
  },
  {
    id: "active",
    eyebrow: "In motion",
    title: "Active",
    statuses: ["Applied", "Under review", "Assessment", "Interview"],
  },
  {
    id: "outcomes",
    eyebrow: "Close the loop",
    title: "Outcomes",
    statuses: ["Offer", "Rejected", "Withdrawn"],
  },
];

function isApplicationList(value: unknown): value is ApplicationListResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "items" in value &&
    Array.isArray(value.items)
  );
}

function isApplicationDetail(
  value: unknown,
): value is ApplicationDetailResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof value.id === "string" &&
    "events" in value &&
    Array.isArray(value.events)
  );
}

function displayDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

function displayDateTime(value: string) {
  return new Intl.DateTimeFormat("en", {
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

function dueLabel(value: string) {
  const date = new Date(value);
  const isOverdue = date.getTime() < Date.now();
  return {
    label: `${isOverdue ? "Overdue" : "Due"} ${displayDate(value)}`,
    isOverdue,
  };
}

function toDateTimeInput(value: string | null | undefined) {
  if (!value) return "";
  const date = new Date(value);
  const offset = date.getTimezoneOffset();
  return new Date(date.getTime() - offset * 60_000).toISOString().slice(0, 16);
}

function statusKey(status: ApplicationStatus) {
  return status.toLowerCase().replaceAll(" ", "-");
}

export function ApplicationTrackerWorkspace() {
  const [state, setState] = useState<TrackerState>({ status: "loading" });
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [details, setDetails] = useState<
    Record<string, ApplicationDetailResponse>
  >({});
  const [detailLoading, setDetailLoading] = useState<Set<string>>(new Set());
  const [transitioning, setTransitioning] = useState<Set<string>>(new Set());
  const [savingPlan, setSavingPlan] = useState<Set<string>>(new Set());
  const [announcement, setAnnouncement] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      try {
        const response = await fetch("/api/applications", {
          cache: "no-store",
          signal: controller.signal,
        });
        const payload: unknown = await response.json();
        if (!response.ok || !isApplicationList(payload)) {
          throw new Error(
            getApiErrorMessage(payload) ??
              "Solara Hire could not load your application tracker.",
          );
        }
        setState({ status: "ready", items: [...payload.items] });
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "Solara Hire could not load your application tracker.",
        });
      }
    })();
    return () => controller.abort();
  }, []);

  const loadDetail = async (applicationId: string) => {
    if (expandedId === applicationId) {
      setExpandedId(null);
      return;
    }
    setExpandedId(applicationId);
    if (details[applicationId]) return;
    setDetailLoading((current) => new Set(current).add(applicationId));
    setAnnouncement("");
    try {
      const response = await fetch(`/api/applications/${applicationId}`, {
        cache: "no-store",
      });
      const payload: unknown = await response.json();
      if (!response.ok || !isApplicationDetail(payload)) {
        throw new Error(
          getApiErrorMessage(payload) ??
            "Solara Hire could not load this application history.",
        );
      }
      setDetails((current) => ({ ...current, [applicationId]: payload }));
    } catch (error) {
      setAnnouncement(
        error instanceof Error
          ? error.message
          : "Solara Hire could not load this application history.",
      );
    } finally {
      setDetailLoading((current) => {
        const next = new Set(current);
        next.delete(applicationId);
        return next;
      });
    }
  };

  const transitionApplication = async (
    event: FormEvent<HTMLFormElement>,
    item: ApplicationResponse,
  ) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const requestedStatus = String(form.get("status")) as ApplicationStatus;
    if (!item.allowed_next_statuses.includes(requestedStatus)) {
      setAnnouncement("Choose one of the available next statuses.");
      return;
    }
    const note = String(form.get("note") ?? "").trim();
    const request: TransitionApplicationRequest = {
      status: requestedStatus,
      note: note || null,
      next_action: item.next_action ?? null,
      next_action_due_at: item.next_action_due_at ?? null,
    };

    setTransitioning((current) => new Set(current).add(item.id));
    setAnnouncement("");
    try {
      const response = await fetch(`/api/applications/${item.id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });
      const payload: unknown = await response.json();
      if (!response.ok || !isApplicationDetail(payload)) {
        throw new Error(
          getApiErrorMessage(payload) ??
            "Solara Hire could not update this application.",
        );
      }
      setDetails((current) => ({ ...current, [item.id]: payload }));
      setState((current) =>
        current.status === "ready"
          ? {
              status: "ready",
              items: current.items.map((application) =>
                application.id === item.id ? payload : application,
              ),
            }
          : current,
      );
      setAnnouncement(
        `${item.job.title} moved to ${payload.status}. The change is in your history.`,
      );
    } catch (error) {
      setAnnouncement(
        error instanceof Error
          ? error.message
          : "Solara Hire could not update this application.",
      );
    } finally {
      setTransitioning((current) => {
        const next = new Set(current);
        next.delete(item.id);
        return next;
      });
    }
  };

  const saveApplicationPlan = async (
    event: FormEvent<HTMLFormElement>,
    item: ApplicationResponse,
  ) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const notes = String(form.get("notes") ?? "").trim();
    const nextAction = String(form.get("next_action") ?? "").trim();
    const dueAt = String(form.get("next_action_due_at") ?? "").trim();
    const request: UpdateApplicationPlanRequest = {
      notes: notes || null,
      next_action: nextAction || null,
      next_action_due_at: dueAt ? new Date(dueAt).toISOString() : null,
    };

    setSavingPlan((current) => new Set(current).add(item.id));
    setAnnouncement("");
    try {
      const response = await fetch(`/api/applications/${item.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });
      const payload: unknown = await response.json();
      if (!response.ok || !isApplicationDetail(payload)) {
        throw new Error(
          getApiErrorMessage(payload) ??
            "Solara Hire could not update this application plan.",
        );
      }
      setDetails((current) => ({ ...current, [item.id]: payload }));
      setState((current) =>
        current.status === "ready"
          ? {
              status: "ready",
              items: current.items.map((application) =>
                application.id === item.id ? payload : application,
              ),
            }
          : current,
      );
      setAnnouncement(
        `${item.job.title} planning details were updated. Its employer-status history is unchanged.`,
      );
      window.dispatchEvent(
        new Event("solarahire:application-plan-updated"),
      );
    } catch (error) {
      setAnnouncement(
        error instanceof Error
          ? error.message
          : "Solara Hire could not update this application plan.",
      );
    } finally {
      setSavingPlan((current) => {
        const next = new Set(current);
        next.delete(item.id);
        return next;
      });
    }
  };

  const items = state.status === "ready" ? state.items : [];

  useEffect(() => {
    if (state.status !== "ready" || !window.location.hash) return;
    const applicationId = window.location.hash.replace("#application-", "");
    if (!state.items.some((item) => item.id === applicationId)) return;
    window.requestAnimationFrame(() => {
      const card = document.getElementById(`application-${applicationId}`);
      card?.scrollIntoView({ block: "center" });
      card?.focus({ preventScroll: true });
    });
  }, [state]);

  const activeCount = items.filter((item) =>
    ["Applied", "Under review", "Assessment", "Interview"].includes(
      item.status,
    ),
  ).length;
  const interviewCount = items.filter(
    (item) => item.status === "Interview",
  ).length;
  const offerCount = items.filter((item) => item.status === "Offer").length;

  return (
    <main id="main-content" className="application-tracker-main">
      <section className="tracker-hero" aria-labelledby="tracker-title">
        <div>
          <span className="review-kicker">
            <span aria-hidden="true">05</span>
            Application command center
          </span>
          <h1 id="tracker-title">
            Keep every move <span>in view.</span>
          </h1>
          <p>
            Turn promising roles into deliberate next steps. You control every
            status change; Solara Hire keeps the evidence trail.
          </p>
        </div>
        <div className="tracker-assurance">
          <span aria-hidden="true">✓</span>
          <div>
            <strong>Nothing moves without you.</strong>
            <span>You confirm employer updates; Solara Hire records them.</span>
          </div>
        </div>
      </section>

      <section className="tracker-workspace" aria-label="Application tracker">
        <div className="tracker-overview">
          <div>
            <span className="micro-label">Tracked</span>
            <strong>{items.length}</strong>
            <small>applications</small>
          </div>
          <div>
            <span className="micro-label">In motion</span>
            <strong>{activeCount}</strong>
            <small>active processes</small>
          </div>
          <div>
            <span className="micro-label">Interviews</span>
            <strong>{interviewCount}</strong>
            <small>current stage</small>
          </div>
          <div>
            <span className="micro-label">Offers</span>
            <strong>{offerCount}</strong>
            <small>outcomes</small>
          </div>
        </div>

        <p className="tracker-announcement" role="status" aria-live="polite">
          {announcement}
        </p>

        {state.status === "loading" && (
          <div className="tracker-state" aria-busy="true">
            <span className="saved-state-mark" aria-hidden="true" />
            <h2>Opening your application workspace.</h2>
            <p>Loading the private history attached to your account.</p>
          </div>
        )}

        {state.status === "error" && (
          <div className="tracker-state is-error">
            <span aria-hidden="true">!</span>
            <h2>Your tracker is temporarily unavailable.</h2>
            <p>{state.message}</p>
            <button
              className="button"
              type="button"
              onClick={() => window.location.reload()}
            >
              Try again
            </button>
          </div>
        )}

        {state.status === "ready" && items.length === 0 && (
          <div className="tracker-empty">
            <div className="tracker-empty-visual" aria-hidden="true">
              <span>01</span>
              <i />
              <span>02</span>
              <i />
              <span>03</span>
            </div>
            <span className="micro-label">A clear starting point</span>
            <h2>Your next application starts with a role worth pursuing.</h2>
            <p>
              Save a role, review it, then choose “Start tracking” when you are
              ready to prepare an application.
            </p>
            <a className="button" href="/saved">
              Review saved roles
              <span aria-hidden="true">→</span>
            </a>
          </div>
        )}

        {state.status === "ready" && items.length > 0 && (
          <div className="tracker-board">
            {TRACKER_GROUPS.map((group) => {
              const groupItems = items.filter((item) =>
                group.statuses.includes(item.status),
              );
              return (
                <section
                  className={`tracker-column tracker-column-${group.id}`}
                  key={group.id}
                  aria-labelledby={`tracker-group-${group.id}`}
                >
                  <div className="tracker-column-heading">
                    <div>
                      <span>{group.eyebrow}</span>
                      <h2 id={`tracker-group-${group.id}`}>{group.title}</h2>
                    </div>
                    <strong>{groupItems.length}</strong>
                  </div>

                  {groupItems.length === 0 ? (
                    <p className="tracker-column-empty">
                      No applications at this stage.
                    </p>
                  ) : (
                    <div className="tracker-card-list">
                      {groupItems.map((item) => {
                        const due = item.next_action_due_at
                          ? dueLabel(item.next_action_due_at)
                          : null;
                        const detail = details[item.id];
                        const isExpanded = expandedId === item.id;
                        return (
                          <article
                            className="tracker-card"
                            id={`application-${item.id}`}
                            tabIndex={-1}
                            key={item.id}
                          >
                            <div className="tracker-card-topline">
                              <span
                                className="tracker-status"
                                data-status={statusKey(item.status)}
                              >
                                {item.status}
                              </span>
                              <small>
                                User confirmed · {displayDate(item.updated_at)}
                              </small>
                            </div>
                            <ProviderAttribution {...item.job} />
                            <h3>{item.job.title}</h3>
                            <p>
                              {item.job.company} · {item.job.location}
                            </p>
                            {item.next_action && (
                              <div className="tracker-next-action">
                                <span>Next action</span>
                                <strong>{item.next_action}</strong>
                                {due && (
                                  <small className={due.isOverdue ? "overdue" : ""}>
                                    {due.label}
                                  </small>
                                )}
                              </div>
                            )}
                            <div className="tracker-card-actions">
                              <button
                                type="button"
                                onClick={() => loadDetail(item.id)}
                                aria-expanded={isExpanded}
                              >
                                {detailLoading.has(item.id)
                                  ? "Loading"
                                  : isExpanded
                                    ? "Close history"
                                    : "History & next step"}
                              </button>
                              <a
                                href={item.job.url}
                                target="_blank"
                                rel="noreferrer"
                                aria-label={`Review ${item.job.title} at ${item.job.company} (opens in a new tab)`}
                              >
                                Review role ↗
                              </a>
                            </div>

                            {isExpanded && (
                              <div className="tracker-card-detail">
                                {detailLoading.has(item.id) ? (
                                  <p>Loading your recorded history…</p>
                                ) : detail ? (
                                  <>
                                    <form
                                      className="tracker-plan-form"
                                      onSubmit={(event) =>
                                        saveApplicationPlan(event, item)
                                      }
                                    >
                                      <div>
                                        <span className="micro-label">
                                          Personal plan
                                        </span>
                                        <p>
                                          These fields guide your work. They do
                                          not claim the employer changed your
                                          status.
                                        </p>
                                      </div>
                                      <label>
                                        Next action
                                        <input
                                          name="next_action"
                                          maxLength={500}
                                          defaultValue={
                                            detail.next_action ?? ""
                                          }
                                          placeholder="Follow up, prepare, or review"
                                        />
                                      </label>
                                      <label>
                                        Deadline
                                        <input
                                          name="next_action_due_at"
                                          type="datetime-local"
                                          defaultValue={toDateTimeInput(
                                            detail.next_action_due_at,
                                          )}
                                        />
                                      </label>
                                      <label>
                                        Private notes
                                        <textarea
                                          name="notes"
                                          maxLength={4000}
                                          defaultValue={detail.notes ?? ""}
                                          placeholder="Context you want to remember"
                                        />
                                      </label>
                                      <button
                                        className="tracker-plan-save"
                                        type="submit"
                                        disabled={savingPlan.has(item.id)}
                                      >
                                        {savingPlan.has(item.id)
                                          ? "Saving plan"
                                          : "Save plan"}
                                      </button>
                                    </form>

                                    {item.allowed_next_statuses.length > 0 ? (
                                      <form
                                        className="tracker-transition-form"
                                        onSubmit={(event) =>
                                          transitionApplication(event, item)
                                        }
                                      >
                                        <span className="micro-label">
                                          Confirm the next move
                                        </span>
                                        <label>
                                          New status
                                          <select
                                            name="status"
                                            defaultValue={
                                              item.allowed_next_statuses[0]
                                            }
                                          >
                                            {item.allowed_next_statuses.map(
                                              (status) => (
                                                <option
                                                  value={status}
                                                  key={status}
                                                >
                                                  {status}
                                                </option>
                                              ),
                                            )}
                                          </select>
                                        </label>
                                        <label>
                                          What changed?
                                          <textarea
                                            name="note"
                                            maxLength={2000}
                                            placeholder="Optional note for your history"
                                          />
                                        </label>
                                        <button
                                          className="button"
                                          type="submit"
                                          disabled={transitioning.has(item.id)}
                                        >
                                          {transitioning.has(item.id)
                                            ? "Recording"
                                            : "Confirm transition"}
                                        </button>
                                      </form>
                                    ) : (
                                      <p className="tracker-terminal-note">
                                        This is a terminal outcome. Its history
                                        remains available for your records.
                                      </p>
                                    )}

                                    <div className="tracker-timeline">
                                      <span className="micro-label">
                                        Recorded history
                                      </span>
                                      <ol>
                                        {[...detail.events]
                                          .reverse()
                                          .map((event) => (
                                            <li key={event.id}>
                                              <i aria-hidden="true" />
                                              <div>
                                                <strong>
                                                  {event.previous_status
                                                    ? `${event.previous_status} → ${event.new_status}`
                                                    : `Started at ${event.new_status}`}
                                                </strong>
                                                <time
                                                  dateTime={event.occurred_at}
                                                >
                                                  {displayDateTime(
                                                    event.occurred_at,
                                                  )}
                                                </time>
                                                {event.note && (
                                                  <p>{event.note}</p>
                                                )}
                                              </div>
                                            </li>
                                          ))}
                                      </ol>
                                    </div>
                                  </>
                                ) : (
                                  <p>History could not be loaded.</p>
                                )}
                              </div>
                            )}
                          </article>
                        );
                      })}
                    </div>
                  )}
                </section>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}
