"use client";

import { useEffect, useState } from "react";

import type {
  SavedJobListResponse,
  SavedJobResponse,
} from "@/lib/api/job-contract";
import { getApiErrorMessage } from "@/lib/api/resume-contract";

type SavedJobsState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; items: SavedJobResponse[] };

function isSavedJobList(value: unknown): value is SavedJobListResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "items" in value &&
    Array.isArray(value.items)
  );
}

function savedDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

export function SavedJobsWorkspace() {
  const [state, setState] = useState<SavedJobsState>({ status: "loading" });
  const [removing, setRemoving] = useState<Set<string>>(new Set());
  const [tracking, setTracking] = useState<Set<string>>(new Set());
  const [trackedJobIds, setTrackedJobIds] = useState<Set<string>>(new Set());
  const [announcement, setAnnouncement] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      try {
        const response = await fetch("/api/saved-jobs", {
          cache: "no-store",
          signal: controller.signal,
        });
        const payload: unknown = await response.json();
        if (!response.ok || !isSavedJobList(payload)) {
          throw new Error(
            getApiErrorMessage(payload) ??
              "Solara Hire could not load your saved roles.",
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
              : "Solara Hire could not load your saved roles.",
        });
      }
    })();
    return () => controller.abort();
  }, []);

  const removeSavedJob = async (item: SavedJobResponse) => {
    const jobId = item.job.id;
    setRemoving((current) => new Set(current).add(jobId));
    setAnnouncement("");
    try {
      const response = await fetch(`/api/saved-jobs/${jobId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        const payload: unknown = await response.json();
        throw new Error(
          getApiErrorMessage(payload) ??
            "Solara Hire could not remove this role.",
        );
      }
      setState((current) =>
        current.status === "ready"
          ? {
              status: "ready",
              items: current.items.filter((saved) => saved.job.id !== jobId),
            }
          : current,
      );
      setAnnouncement(`${item.job.title} was removed from saved roles.`);
    } catch (error) {
      setAnnouncement(
        error instanceof Error
          ? error.message
          : "Solara Hire could not remove this role.",
      );
    } finally {
      setRemoving((current) => {
        const next = new Set(current);
        next.delete(jobId);
        return next;
      });
    }
  };

  const startTracking = async (item: SavedJobResponse) => {
    const jobId = item.job.id;
    setTracking((current) => new Set(current).add(jobId));
    setAnnouncement("");
    try {
      const response = await fetch("/api/applications", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: jobId,
          notes: item.notes,
          next_action: "Review the role and prepare application evidence",
          next_action_due_at: null,
          resume_id: null,
        }),
      });
      const payload: unknown = await response.json();
      const alreadyTracked =
        typeof payload === "object" &&
        payload !== null &&
        "code" in payload &&
        payload.code === "application_already_exists";
      if (!response.ok && !alreadyTracked) {
        throw new Error(
          getApiErrorMessage(payload) ??
            "Solara Hire could not add this role to your tracker.",
        );
      }
      setTrackedJobIds((current) => new Set(current).add(jobId));
      setAnnouncement(
        alreadyTracked
          ? `${item.job.title} is already in your application tracker.`
          : `${item.job.title} is ready in your application tracker.`,
      );
    } catch (error) {
      setAnnouncement(
        error instanceof Error
          ? error.message
          : "Solara Hire could not add this role to your tracker.",
      );
    } finally {
      setTracking((current) => {
        const next = new Set(current);
        next.delete(jobId);
        return next;
      });
    }
  };

  return (
    <main id="main-content" className="saved-jobs-main">
      <section className="saved-jobs-hero" aria-labelledby="saved-jobs-title">
        <span className="review-kicker">
          <span aria-hidden="true">04</span>
          Your shortlist
        </span>
        <h1 id="saved-jobs-title">
          Roles worth <span>another look.</span>
        </h1>
        <p>
          Keep promising opportunities together, then return with context
          before deciding whether to apply.
        </p>
        <div className="saved-jobs-principle">
          <span aria-hidden="true">✓</span>
          <div>
            <strong>Saved by you. Never applied by us.</strong>
            <span>Every next step remains review-first and user-controlled.</span>
          </div>
        </div>
      </section>

      <section className="saved-jobs-panel" aria-label="Saved roles">
        <div className="saved-jobs-panel-heading">
          <div>
            <span className="micro-label">Account library</span>
            <h2>Your saved roles</h2>
          </div>
          {state.status === "ready" && (
            <span className="saved-count">
              {state.items.length} {state.items.length === 1 ? "role" : "roles"}
            </span>
          )}
        </div>

        <p className="saved-announcement" role="status" aria-live="polite">
          {announcement}
        </p>

        {state.status === "loading" && (
          <div className="saved-state" aria-busy="true">
            <span className="saved-state-mark" aria-hidden="true" />
            <h3>Opening your shortlist.</h3>
            <p>Loading only the roles attached to your verified account.</p>
          </div>
        )}

        {state.status === "error" && (
          <div className="saved-state is-error">
            <span className="saved-state-symbol" aria-hidden="true">
              !
            </span>
            <h3>Your shortlist is temporarily unavailable.</h3>
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

        {state.status === "ready" && state.items.length === 0 && (
          <div className="saved-state is-empty">
            <span className="saved-state-symbol" aria-hidden="true">
              +
            </span>
            <h3>Your shortlist has room.</h3>
            <p>
              Run a focused search and save the roles that deserve a closer
              review.
            </p>
            <a className="button" href="/workspace">
              Find roles
              <span aria-hidden="true">→</span>
            </a>
          </div>
        )}

        {state.status === "ready" && state.items.length > 0 && (
          <div className="saved-role-list">
            {state.items.map((item, index) => (
              <article className="saved-role-card" key={item.job.id}>
                <div className="saved-role-index">
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <small>Saved {savedDate(item.created_at)}</small>
                </div>
                <div className="saved-role-content">
                  <span className="job-source">
                    {item.job.source_name ?? item.job.source}
                  </span>
                  <h3>{item.job.title}</h3>
                  <p>
                    {item.job.company} · {item.job.location}
                  </p>
                  <div className="job-facts">
                    <span>{item.job.employment_type}</span>
                    <span>{item.job.experience_level}</span>
                  </div>
                  {item.notes && <p className="saved-role-notes">{item.notes}</p>}
                  <div className="saved-role-actions">
                    <button
                      className="saved-remove"
                      type="button"
                      disabled={removing.has(item.job.id)}
                      onClick={() => removeSavedJob(item)}
                    >
                      {removing.has(item.job.id) ? "Removing" : "Remove"}
                    </button>
                    {trackedJobIds.has(item.job.id) ? (
                      <a className="saved-track-link" href="/applications">
                        Open tracker
                        <span aria-hidden="true">→</span>
                      </a>
                    ) : (
                      <button
                        className="saved-track-link"
                        type="button"
                        disabled={tracking.has(item.job.id)}
                        onClick={() => startTracking(item)}
                      >
                        {tracking.has(item.job.id)
                          ? "Starting"
                          : "Start tracking"}
                      </button>
                    )}
                    <a
                      className="button"
                      href={item.job.url}
                      target="_blank"
                      rel="noreferrer"
                      aria-label={`Review ${item.job.title} at ${item.job.company} (opens in a new tab)`}
                    >
                      Review role
                      <span aria-hidden="true">↗</span>
                    </a>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
