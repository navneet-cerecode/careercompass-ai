"use client";

import { useState } from "react";

import type {
  TailoredResumeResponse,
  TailoredResumeSelectionsRequest,
  TailoredResumeVersionListResponse,
} from "@/lib/api/job-contract";
import { getApiErrorMessage } from "@/lib/api/resume-contract";

type TailoredResumeWorkspaceProps = {
  planId: string;
  jobTitle: string;
};

type WorkspaceState =
  | { status: "idle" }
  | { status: "loading" }
  | {
      status: "ready";
      draft: TailoredResumeResponse;
      selections: TailoredResumeSelectionsRequest;
      versions: TailoredResumeResponse[];
      saving: boolean;
      approving: boolean;
      message: string | null;
    }
  | { status: "error"; message: string };

const sections = ["skills", "experience", "projects"] as const;
type ReviewSection = (typeof sections)[number];

function isTailoredResume(value: unknown): value is TailoredResumeResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof value.id === "string" &&
    "original" in value &&
    "suggested" in value &&
    "accepted" in value &&
    "selections" in value &&
    typeof value.selections === "object" &&
    value.selections !== null
  );
}

function isVersionList(value: unknown): value is TailoredResumeVersionListResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "items" in value &&
    Array.isArray(value.items) &&
    value.items.every(isTailoredResume)
  );
}

function sectionItems(
  draft: TailoredResumeResponse,
  source: "original" | "suggested" | "accepted",
  section: ReviewSection,
) {
  const value = draft[source][section];
  return section === "skills"
    ? (value as TailoredResumeResponse["accepted"]["skills"]).map(
        (skill) => skill.name,
      )
    : (value as string[]);
}

function ReviewList({ items }: { items: string[] }) {
  if (items.length === 0) return <p className="tailored-empty">No content in this section.</p>;
  return (
    <ol>
      {items.map((item, index) => (
        <li key={`${index}-${item}`}>{item}</li>
      ))}
    </ol>
  );
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

export function TailoredResumeWorkspace({
  planId,
  jobTitle,
}: TailoredResumeWorkspaceProps) {
  const [state, setState] = useState<WorkspaceState>({ status: "idle" });
  const [confirmed, setConfirmed] = useState(false);

  const loadVersions = async (draftId: string) => {
    const response = await fetch(`/api/tailored-resumes/${draftId}/versions`, {
      cache: "no-store",
    });
    const payload = await readJson(response);
    return response.ok && isVersionList(payload) ? payload.items : [];
  };

  const openWorkspace = async () => {
    setState({ status: "loading" });
    try {
      const response = await fetch("/api/tailored-resumes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_id: planId }),
      });
      const payload = await readJson(response);
      if (!response.ok || !isTailoredResume(payload)) {
        throw new Error(
          getApiErrorMessage(payload) ?? "Solara Hire could not open this review workspace.",
        );
      }
      const versions = await loadVersions(payload.id);
      setState({
        status: "ready",
        draft: payload,
        selections: payload.selections,
        versions,
        saving: false,
        approving: false,
        message: null,
      });
      setConfirmed(false);
    } catch (error) {
      setState({
        status: "error",
        message:
          error instanceof Error
            ? error.message
            : "Solara Hire could not open this review workspace.",
      });
    }
  };

  if (state.status === "idle") {
    return (
      <button className="button tailored-open-button" type="button" onClick={openWorkspace}>
        Compare and prepare export
      </button>
    );
  }

  if (state.status === "loading") {
    return (
      <button className="button tailored-open-button" type="button" disabled>
        Opening review workspace
      </button>
    );
  }

  if (state.status === "error") {
    return (
      <div className="tailored-workspace-error" role="alert">
        <span>{state.message}</span>
        <button type="button" onClick={openWorkspace}>Try again</button>
      </div>
    );
  }

  const dirty = sections.some(
    (section) => state.selections[section] !== state.draft.selections[section],
  );
  const verified = state.draft.verification_status === "user_verified";

  const choose = (section: ReviewSection, choice: "original" | "suggested") => {
    setConfirmed(false);
    setState((current) =>
      current.status === "ready"
        ? {
            ...current,
            selections: { ...current.selections, [section]: choice },
            message: null,
          }
        : current,
    );
  };

  const saveRevision = async () => {
    if (!dirty) return;
    setState({ ...state, saving: true, message: null });
    try {
      const response = await fetch(`/api/tailored-resumes/${state.draft.id}/revisions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state.selections),
      });
      const payload = await readJson(response);
      if (!response.ok || !isTailoredResume(payload)) {
        throw new Error(
          getApiErrorMessage(payload) ?? "Solara Hire could not save this review.",
        );
      }
      const versions = await loadVersions(payload.id);
      setState({
        status: "ready",
        draft: payload,
        selections: payload.selections,
        versions,
        saving: false,
        approving: false,
        message: `Version ${payload.version} saved. Review it before confirming.`,
      });
    } catch (error) {
      setState({
        ...state,
        saving: false,
        message:
          error instanceof Error ? error.message : "Solara Hire could not save this review.",
      });
    }
  };

  const approve = async () => {
    if (!confirmed || dirty) return;
    setState({ ...state, approving: true, message: null });
    try {
      const response = await fetch(`/api/tailored-resumes/${state.draft.id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirm_factual_accuracy: true }),
      });
      const payload = await readJson(response);
      if (!response.ok || !isTailoredResume(payload)) {
        throw new Error(
          getApiErrorMessage(payload) ?? "Solara Hire could not confirm this version.",
        );
      }
      const versions = await loadVersions(payload.id);
      setState({
        status: "ready",
        draft: payload,
        selections: payload.selections,
        versions,
        saving: false,
        approving: false,
        message: "Factual review confirmed. PDF and DOCX exports are ready.",
      });
    } catch (error) {
      setState({
        ...state,
        approving: false,
        message:
          error instanceof Error
            ? error.message
            : "Solara Hire could not confirm this version.",
      });
    }
  };

  return (
    <section className="tailored-workspace" aria-label={`Resume review for ${jobTitle}`}>
      <header>
        <div>
          <span className="micro-label">Version {state.draft.version}</span>
          <h5>Original. Suggested. Your decision.</h5>
        </div>
        <span className={`tailored-status ${verified ? "is-verified" : ""}`}>
          {verified ? "Factual review confirmed" : "Review pending"}
        </span>
      </header>

      <p className="tailored-instructions">
        Choose the ordering you want for each section. Solara Hire never adds a skill,
        responsibility, metric, employer, project, or date.
      </p>

      <div className="tailored-comparison">
        {sections.map((section) => (
          <fieldset key={section}>
            <legend>{section}</legend>
            <label
              className={state.selections[section] === "original" ? "is-selected" : ""}
            >
              <input
                type="radio"
                name={`${state.draft.id}-${section}`}
                value="original"
                checked={state.selections[section] === "original"}
                onChange={() => choose(section, "original")}
              />
              <span>Original order</span>
              <ReviewList items={sectionItems(state.draft, "original", section)} />
            </label>
            <label
              className={state.selections[section] === "suggested" ? "is-selected" : ""}
            >
              <input
                type="radio"
                name={`${state.draft.id}-${section}`}
                value="suggested"
                checked={state.selections[section] === "suggested"}
                onChange={() => choose(section, "suggested")}
              />
              <span>Suggested order</span>
              <ReviewList items={sectionItems(state.draft, "suggested", section)} />
            </label>
          </fieldset>
        ))}
      </div>

      <details className="tailored-accepted-preview" open>
        <summary>
          Accepted resume snapshot
          {dirty && <span>Unsaved choices</span>}
        </summary>
        <div>
          {sections.map((section) => (
            <section key={section} aria-label={`Accepted ${section}`}>
              <span className="micro-label">{section}</span>
              <ReviewList
                items={sectionItems(
                  state.draft,
                  state.selections[section],
                  section,
                )}
              />
            </section>
          ))}
        </div>
      </details>

      <div className="tailored-review-actions">
        <button
          className="button"
          type="button"
          disabled={!dirty || state.saving}
          onClick={saveRevision}
        >
          {state.saving ? "Saving version" : "Save choices as new version"}
        </button>
        {!verified && (
          <label className="factual-confirmation">
            <input
              type="checkbox"
              checked={confirmed}
              disabled={dirty}
              onChange={(event) => setConfirmed(event.target.checked)}
            />
            <span>I reviewed every accepted section and confirm it is factually accurate.</span>
          </label>
        )}
        {!verified && (
          <button
            className="button tailored-approve-button"
            type="button"
            disabled={!confirmed || dirty || state.approving}
            onClick={approve}
          >
            {state.approving ? "Confirming review" : "Confirm factual review"}
          </button>
        )}
        {verified && (
          <div className="tailored-downloads">
            <a href={`/api/tailored-resumes/${state.draft.id}/export?format=pdf`}>
              Download PDF
            </a>
            <a href={`/api/tailored-resumes/${state.draft.id}/export?format=docx`}>
              Download DOCX
            </a>
          </div>
        )}
      </div>

      <p className="tailored-feedback" role="status" aria-live="polite">
        {state.message}
      </p>

      <details className="tailored-history">
        <summary>Version history ({state.versions.length})</summary>
        <ol>
          {state.versions.map((version) => (
            <li key={version.id}>
              <strong>Version {version.version}</strong>
              <span>
                {version.verification_status === "user_verified"
                  ? "Factual review confirmed"
                  : "Pending review"}
              </span>
            </li>
          ))}
        </ol>
      </details>
    </section>
  );
}
