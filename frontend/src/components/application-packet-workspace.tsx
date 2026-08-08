"use client";

import { useState } from "react";

import type {
  ApplicationPacketResponse,
  ApplicationResponse,
  ConfirmExternalSubmissionRequest,
  UpdateApplicationPacketRequest,
} from "@/lib/api/job-contract";
import { getApiErrorMessage } from "@/lib/api/resume-contract";

type PacketState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; packet: ApplicationPacketResponse; dirty: boolean };

type ApplicationPacketWorkspaceProps = {
  application: ApplicationResponse;
  onApplicationChanged: (applicationId: string) => Promise<void>;
};

function isPacket(value: unknown): value is ApplicationPacketResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "application_id" in value &&
    "blockers" in value &&
    Array.isArray(value.blockers)
  );
}

const REVIEW_STEPS: Array<{
  key: keyof UpdateApplicationPacketRequest;
  label: string;
  description: string;
}> = [
  {
    key: "job_details_reviewed",
    label: "I reviewed the role and employer page",
    description: "The title, location, requirements, and application link look correct.",
  },
  {
    key: "resume_reviewed",
    label: "I reviewed the selected resume",
    description: "Every claim is accurate and the document is ready to share.",
  },
  {
    key: "cover_letter_reviewed",
    label: "I reviewed the selected cover letter",
    description: "Required only when a cover letter is included.",
  },
  {
    key: "employer_questions_reviewed",
    label: "I reviewed the employer's application questions",
    description: "You will answer and submit them yourself on the employer site.",
  },
];

export function ApplicationPacketWorkspace({
  application,
  onApplicationChanged,
}: ApplicationPacketWorkspaceProps) {
  const [state, setState] = useState<PacketState>({ status: "idle" });
  const [busy, setBusy] = useState(false);
  const [submissionConfirmed, setSubmissionConfirmed] = useState(false);
  const [message, setMessage] = useState("");

  const requestPacket = async (
    path: string,
    init: RequestInit,
    fallback: string,
  ) => {
    const response = await fetch(path, init);
    const payload: unknown = await response.json();
    if (!response.ok || !isPacket(payload)) {
      throw new Error(getApiErrorMessage(payload) ?? fallback);
    }
    return payload;
  };

  const openPacket = async () => {
    setState({ status: "loading" });
    setMessage("");
    try {
      const packet = await requestPacket(
        `/api/applications/${application.id}/packet`,
        { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" },
        "Solara Hire could not prepare this application packet.",
      );
      setState({ status: "ready", packet, dirty: false });
    } catch (error) {
      setState({
        status: "error",
        message: error instanceof Error ? error.message : "The packet could not be loaded.",
      });
    }
  };

  const updateDraft = (
    changes: Partial<ApplicationPacketResponse>,
  ) => {
    setState((current) =>
      current.status === "ready"
        ? {
            status: "ready",
            packet: { ...current.packet, ...changes },
            dirty: true,
          }
        : current,
    );
    setMessage("");
  };

  const saveReview = async () => {
    if (state.status !== "ready") return;
    setBusy(true);
    setMessage("");
    const packet = state.packet;
    const request: UpdateApplicationPacketRequest = {
      tailored_resume_id: packet.tailored_resume_id,
      cover_letter_id: packet.cover_letter_id,
      job_details_reviewed: packet.job_details_reviewed,
      resume_reviewed: packet.resume_reviewed,
      cover_letter_reviewed: packet.cover_letter_id
        ? packet.cover_letter_reviewed
        : false,
      employer_questions_reviewed: packet.employer_questions_reviewed,
    };
    try {
      const saved = await requestPacket(
        `/api/applications/${application.id}/packet`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request),
        },
        "Solara Hire could not save this review.",
      );
      setState({ status: "ready", packet: saved, dirty: false });
      setMessage(
        saved.blockers.length === 0
          ? "Review saved. This packet is ready for your final confirmation."
          : "Review saved. Complete the remaining checks when you are ready.",
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The review could not be saved.");
    } finally {
      setBusy(false);
    }
  };

  const markReady = async () => {
    if (state.status !== "ready" || state.dirty) return;
    setBusy(true);
    setMessage("");
    try {
      const packet = await requestPacket(
        `/api/applications/${application.id}/packet/ready`,
        { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" },
        "Solara Hire could not mark this packet ready.",
      );
      setState({ status: "ready", packet, dirty: false });
      setMessage("Packet locked. Continue on the employer site when you choose.");
      await onApplicationChanged(application.id);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The packet could not be locked.");
    } finally {
      setBusy(false);
    }
  };

  const confirmSubmitted = async () => {
    if (state.status !== "ready" || !submissionConfirmed) return;
    setBusy(true);
    setMessage("");
    const request: ConfirmExternalSubmissionRequest = {
      confirm_external_submission: true,
    };
    try {
      const packet = await requestPacket(
        `/api/applications/${application.id}/packet/submitted`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request),
        },
        "Solara Hire could not record your submission.",
      );
      setState({ status: "ready", packet, dirty: false });
      setMessage("Submission recorded from your confirmation.");
      await onApplicationChanged(application.id);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The submission could not be recorded.");
    } finally {
      setBusy(false);
    }
  };

  if (state.status === "idle") {
    return (
      <section className="application-packet application-packet-intro">
        <div>
          <span className="micro-label">Assisted application</span>
          <h4>Build a reviewed application packet.</h4>
          <p>
            Choose verified documents, check the employer requirements, and keep the final
            submission in your hands.
          </p>
        </div>
        <button type="button" onClick={openPacket}>
          Build application packet
        </button>
      </section>
    );
  }

  if (state.status === "loading") {
    return <p className="application-packet-loading">Preparing your reviewed packet...</p>;
  }

  if (state.status === "error") {
    return (
      <section className="application-packet application-packet-error">
        <p>{state.message}</p>
        <button type="button" onClick={openPacket}>Try again</button>
      </section>
    );
  }

  const { packet, dirty } = state;
  const isLocked = packet.ready_at !== null;

  return (
    <section className="application-packet" aria-labelledby={`packet-${application.id}`}>
      <header className="application-packet-heading">
        <div>
          <span className="micro-label">Application packet</span>
          <h4 id={`packet-${application.id}`}>
            {isLocked ? "Reviewed and ready" : "Review before you continue"}
          </h4>
        </div>
        <span className="application-packet-state">
          {isLocked ? "Locked" : `${packet.blockers.length} checks left`}
        </span>
      </header>

      <div className="application-packet-documents">
        <label>
          Resume for this application
          <select
            value={packet.tailored_resume_id ?? "original"}
            disabled={isLocked}
            onChange={(event) =>
              updateDraft({
                tailored_resume_id:
                  event.target.value === "original" ? null : event.target.value,
                resume_reviewed: false,
              })
            }
          >
            <option value="original">Original uploaded resume</option>
            {packet.available_tailored_resumes.map((resume) => (
              <option value={resume.id} key={resume.id}>
                Verified tailored resume - version {resume.version}
              </option>
            ))}
          </select>
        </label>
        <label>
          Cover letter
          <select
            value={packet.cover_letter_id ?? "none"}
            disabled={isLocked}
            onChange={(event) =>
              updateDraft({
                cover_letter_id: event.target.value === "none" ? null : event.target.value,
                cover_letter_reviewed: false,
              })
            }
          >
            <option value="none">No cover letter</option>
            {packet.available_cover_letters.map((letter) => (
              <option value={letter.id} key={letter.id}>
                Verified cover letter - version {letter.version}
              </option>
            ))}
          </select>
        </label>
      </div>

      {(packet.tailored_resume_id || packet.cover_letter_id) && (
        <div className="application-packet-downloads">
          <span>Verified files</span>
          {packet.tailored_resume_id && (
            <a href={`/api/tailored-resumes/${packet.tailored_resume_id}/export?format=pdf`}>
              Resume PDF
            </a>
          )}
          {packet.cover_letter_id && (
            <a href={`/api/cover-letters/${packet.cover_letter_id}/export?format=pdf`}>
              Cover letter PDF
            </a>
          )}
        </div>
      )}

      <div className="application-packet-checklist">
        {REVIEW_STEPS.map((step, index) => {
          const coverLetterStep = step.key === "cover_letter_reviewed";
          const disabled = isLocked || (coverLetterStep && !packet.cover_letter_id);
          return (
            <label key={step.key} data-disabled={disabled || undefined}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <input
                type="checkbox"
                checked={Boolean(packet[step.key])}
                disabled={disabled}
                onChange={(event) => updateDraft({ [step.key]: event.target.checked })}
              />
              <span>
                <strong>{step.label}</strong>
                <small>{step.description}</small>
              </span>
            </label>
          );
        })}
      </div>

      {!isLocked ? (
        <div className="application-packet-actions">
          <button type="button" onClick={saveReview} disabled={busy || !dirty}>
            {busy ? "Saving..." : "Save review"}
          </button>
          <button
            className="application-packet-primary"
            type="button"
            onClick={markReady}
            disabled={busy || dirty || !packet.can_mark_ready}
          >
            Mark packet ready
          </button>
        </div>
      ) : packet.can_confirm_submitted ? (
        <div className="application-packet-submit">
          <div>
            <a href={application.job.url} target="_blank" rel="noreferrer">
              Continue on employer site
              <span aria-hidden="true">↗</span>
            </a>
            <small>Solara Hire does not submit or answer employer questions for you.</small>
          </div>
          <label>
            <input
              type="checkbox"
              checked={submissionConfirmed}
              onChange={(event) => setSubmissionConfirmed(event.target.checked)}
            />
            I submitted this application on the employer site
          </label>
          <button
            type="button"
            onClick={confirmSubmitted}
            disabled={busy || !submissionConfirmed}
          >
            {busy ? "Recording..." : "Record my submission"}
          </button>
        </div>
      ) : (
        <p className="application-packet-complete">Submission recorded. Employer updates remain yours to confirm.</p>
      )}

      <p className="application-packet-message" role="status" aria-live="polite">
        {message}
      </p>
    </section>
  );
}
