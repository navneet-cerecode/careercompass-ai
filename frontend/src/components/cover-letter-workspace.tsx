"use client";

import { useState } from "react";

import type {
  CoverLetterContentRequest,
  CoverLetterResponse,
  CoverLetterVersionListResponse,
} from "@/lib/api/job-contract";
import { getApiErrorMessage } from "@/lib/api/resume-contract";

type CoverLetterWorkspaceProps = {
  planId: string;
  jobTitle: string;
};

type WorkspaceState =
  | { status: "idle" }
  | { status: "loading" }
  | {
      status: "ready";
      draft: CoverLetterResponse;
      content: CoverLetterContentRequest;
      versions: CoverLetterResponse[];
      saving: boolean;
      approving: boolean;
      message: string | null;
    }
  | { status: "error"; message: string };

const editableFields = [
  { key: "salutation", label: "Greeting", rows: 1 },
  { key: "opening", label: "Opening", rows: 3 },
  { key: "evidence_paragraph", label: "Verified evidence", rows: 5 },
  { key: "motivation_paragraph", label: "Motivation", rows: 4 },
  { key: "closing_paragraph", label: "Closing", rows: 4 },
  { key: "sign_off", label: "Sign-off", rows: 1 },
] as const satisfies ReadonlyArray<{
  key: keyof CoverLetterContentRequest;
  label: string;
  rows: number;
}>;

function isCoverLetter(value: unknown): value is CoverLetterResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof value.id === "string" &&
    "accepted" in value &&
    typeof value.accepted === "object" &&
    value.accepted !== null &&
    "evidence" in value &&
    Array.isArray(value.evidence)
  );
}

function isVersionList(value: unknown): value is CoverLetterVersionListResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "items" in value &&
    Array.isArray(value.items) &&
    value.items.every(isCoverLetter)
  );
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

export function CoverLetterWorkspace({ planId, jobTitle }: CoverLetterWorkspaceProps) {
  const [state, setState] = useState<WorkspaceState>({ status: "idle" });
  const [confirmed, setConfirmed] = useState(false);

  const loadVersions = async (draftId: string) => {
    const response = await fetch(`/api/cover-letters/${draftId}/versions`, {
      cache: "no-store",
    });
    const payload = await readJson(response);
    return response.ok && isVersionList(payload) ? payload.items : [];
  };

  const openWorkspace = async () => {
    setState({ status: "loading" });
    try {
      const response = await fetch("/api/cover-letters", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_id: planId }),
      });
      const payload = await readJson(response);
      if (!response.ok || !isCoverLetter(payload)) {
        throw new Error(
          getApiErrorMessage(payload) ?? "Solara Hire could not prepare this cover letter.",
        );
      }
      const versions = await loadVersions(payload.id);
      setState({
        status: "ready",
        draft: payload,
        content: payload.accepted,
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
            : "Solara Hire could not prepare this cover letter.",
      });
    }
  };

  if (state.status === "idle") {
    return (
      <button className="button cover-letter-open-button" type="button" onClick={openWorkspace}>
        Draft from verified evidence
      </button>
    );
  }

  if (state.status === "loading") {
    return (
      <button className="button cover-letter-open-button" type="button" disabled>
        Preparing cover letter
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

  const dirty = JSON.stringify(state.content) !== JSON.stringify(state.draft.accepted);
  const verified = state.draft.verification_status === "user_verified";

  const edit = (key: keyof CoverLetterContentRequest, value: string) => {
    setConfirmed(false);
    setState((current) =>
      current.status === "ready"
        ? {
            ...current,
            content: { ...current.content, [key]: value },
            message: null,
          }
        : current,
    );
  };

  const saveRevision = async () => {
    if (!dirty) return;
    setState({ ...state, saving: true, message: null });
    try {
      const response = await fetch(`/api/cover-letters/${state.draft.id}/revisions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state.content),
      });
      const payload = await readJson(response);
      if (!response.ok || !isCoverLetter(payload)) {
        throw new Error(
          getApiErrorMessage(payload) ?? "Solara Hire could not save this version.",
        );
      }
      const versions = await loadVersions(payload.id);
      setState({
        status: "ready",
        draft: payload,
        content: payload.accepted,
        versions,
        saving: false,
        approving: false,
        message: `Version ${payload.version} saved. Review every sentence before confirming.`,
      });
    } catch (error) {
      setState({
        ...state,
        saving: false,
        message:
          error instanceof Error ? error.message : "Solara Hire could not save this version.",
      });
    }
  };

  const approve = async () => {
    if (!confirmed || dirty) return;
    setState({ ...state, approving: true, message: null });
    try {
      const response = await fetch(`/api/cover-letters/${state.draft.id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirm_factual_accuracy: true }),
      });
      const payload = await readJson(response);
      if (!response.ok || !isCoverLetter(payload)) {
        throw new Error(
          getApiErrorMessage(payload) ?? "Solara Hire could not confirm this version.",
        );
      }
      const versions = await loadVersions(payload.id);
      setState({
        status: "ready",
        draft: payload,
        content: payload.accepted,
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
          error instanceof Error ? error.message : "Solara Hire could not confirm this version.",
      });
    }
  };

  return (
    <section className="cover-letter-workspace" aria-label={`Cover letter review for ${jobTitle}`}>
      <header>
        <div>
          <span className="micro-label">Cover letter · version {state.draft.version}</span>
          <h5>Every sentence stays under your control.</h5>
        </div>
        <span className={`tailored-status ${verified ? "is-verified" : ""}`}>
          {verified ? "Factual review confirmed" : "Review pending"}
        </span>
      </header>

      <p className="cover-letter-assurance">
        The starting draft uses only the target job and evidence from your uploaded résumé.
        Edit freely, then verify every claim before exporting.
      </p>

      <div className="cover-letter-layout">
        <form className="cover-letter-editor" onSubmit={(event) => event.preventDefault()}>
          <div className="cover-letter-address">
            <strong>{state.content.job_title}</strong>
            <span>{state.content.company_name}</span>
          </div>
          {editableFields.map((field) => (
            <label key={field.key}>
              <span>{field.label}</span>
              <textarea
                rows={field.rows}
                value={state.content[field.key] ?? ""}
                onChange={(event) => edit(field.key, event.target.value)}
                maxLength={field.key === "evidence_paragraph" ? 2500 : 1500}
                required
              />
            </label>
          ))}
          <p className="cover-letter-signature">{state.content.candidate_name}</p>
        </form>

        <aside className="cover-letter-evidence" aria-label="Verified source evidence">
          <h6>Evidence ledger</h6>
          <p>These are the verified facts used in the starting draft.</p>
          {state.draft.evidence.length > 0 ? (
            <ol>
              {state.draft.evidence.map((item) => (
                <li key={`${item.kind}-${item.source_index}-${item.source_text}`}>
                  <span>{item.kind}</span>
                  <p>{item.source_text}</p>
                </li>
              ))}
            </ol>
          ) : (
            <p>No direct evidence was selected. Review the generic draft carefully.</p>
          )}
          <details>
            <summary>Starting suggestion</summary>
            <p>{state.draft.suggested.opening}</p>
            <p>{state.draft.suggested.evidence_paragraph}</p>
            <p>{state.draft.suggested.motivation_paragraph}</p>
          </details>
        </aside>
      </div>

      <div className="tailored-review-actions">
        <button className="button" type="button" disabled={!dirty || state.saving} onClick={saveRevision}>
          {state.saving ? "Saving version" : "Save edits as new version"}
        </button>
        {!verified && (
          <label className="factual-confirmation">
            <input
              type="checkbox"
              checked={confirmed}
              disabled={dirty}
              onChange={(event) => setConfirmed(event.target.checked)}
            />
            <span>I reviewed every sentence and confirm all candidate claims are accurate.</span>
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
            <a href={`/api/cover-letters/${state.draft.id}/export?format=pdf`}>Download PDF</a>
            <a href={`/api/cover-letters/${state.draft.id}/export?format=docx`}>Download DOCX</a>
          </div>
        )}
      </div>

      <p className="tailored-feedback" role="status" aria-live="polite">{state.message}</p>

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
