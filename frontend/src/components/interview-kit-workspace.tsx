"use client";

import { useState } from "react";

import type {
  ApplicationResponse,
  InterviewKitResponse,
  UpdateInterviewKitRequest,
} from "@/lib/api/job-contract";
import { getApiErrorMessage } from "@/lib/api/resume-contract";

type KitState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; kit: InterviewKitResponse };

function isInterviewKit(value: unknown): value is InterviewKitResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "questions" in value &&
    Array.isArray(value.questions) &&
    "responses" in value
  );
}

function categoryLabel(category: string) {
  return category.replaceAll("_", " ");
}

export function InterviewKitWorkspace({
  application,
}: {
  application: ApplicationResponse;
}) {
  const [state, setState] = useState<KitState>({ status: "idle" });
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const open = async () => {
    setState({ status: "loading" });
    setMessage("");
    try {
      let response = await fetch(
        `/api/applications/${application.id}/interview-kit`,
        { cache: "no-store" },
      );
      if (response.status === 404) {
        response = await fetch(
          `/api/applications/${application.id}/interview-kit`,
          { method: "POST" },
        );
      }
      const payload: unknown = await response.json();
      if (!response.ok || !isInterviewKit(payload)) {
        throw new Error(
          getApiErrorMessage(payload) ??
            "Solara Hire could not prepare these interview questions.",
        );
      }
      setResponses({ ...payload.responses });
      setState({ status: "ready", kit: payload });
    } catch (error) {
      setState({
        status: "error",
        message:
          error instanceof Error
            ? error.message
            : "Solara Hire could not prepare these interview questions.",
      });
    }
  };

  const save = async (confirmReviewed: boolean) => {
    setSaving(true);
    setMessage("");
    const request: UpdateInterviewKitRequest = {
      responses,
      confirm_reviewed: confirmReviewed,
    };
    try {
      const response = await fetch(
        `/api/applications/${application.id}/interview-kit`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request),
        },
      );
      const payload: unknown = await response.json();
      if (!response.ok || !isInterviewKit(payload)) {
        throw new Error(
          getApiErrorMessage(payload) ??
            "Solara Hire could not save your interview notes.",
        );
      }
      setResponses({ ...payload.responses });
      setState({ status: "ready", kit: payload });
      setMessage(
        confirmReviewed
          ? "Notes saved and marked as fact-checked by you."
          : "Draft notes saved. Employer status is unchanged.",
      );
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Solara Hire could not save your interview notes.",
      );
    } finally {
      setSaving(false);
    }
  };

  if (state.status === "idle") {
    return (
      <section className="interview-kit-intro">
        <div>
          <h4>Prepare without inventing a script.</h4>
          <p>
            Build answers from your verified resume and this role. This is
            preparation only; it does not mean the employer scheduled an interview.
          </p>
        </div>
        <button type="button" onClick={open}>
          Prepare for interview
        </button>
      </section>
    );
  }

  if (state.status === "loading") {
    return <p className="interview-kit-loading">Building evidence prompts…</p>;
  }

  if (state.status === "error") {
    return (
      <section className="interview-kit-error">
        <p>{state.message}</p>
        <button type="button" onClick={open}>Try again</button>
      </section>
    );
  }

  return (
    <section className="interview-kit" aria-labelledby={`interview-kit-${application.id}`}>
      <header>
        <div>
          <h4 id={`interview-kit-${application.id}`}>Your interview evidence room</h4>
          <p>
            Solara Hire proposes the questions. You write and verify every answer.
          </p>
        </div>
        <span data-reviewed={Boolean(state.kit.reviewed_at)}>
          {state.kit.reviewed_at ? "Reviewed by you" : "Draft"}
        </span>
      </header>

      <ol className="interview-question-list">
        {state.kit.questions.map((question, index) => (
          <li key={question.id}>
            <span className="interview-question-number" aria-hidden="true">
              {String(index + 1).padStart(2, "0")}
            </span>
            <div>
              <small>{categoryLabel(question.category)}</small>
              <h5>{question.question}</h5>
              <p>{question.why_it_matters}</p>
              <details>
                <summary>Resume evidence to consider</summary>
                <ul>
                  {question.evidence_prompts.map((prompt) => (
                    <li key={prompt}>{prompt}</li>
                  ))}
                </ul>
              </details>
              <label>
                Your notes
                <textarea
                  value={responses[question.id] ?? ""}
                  maxLength={4000}
                  placeholder="Write only what you can support in a real conversation."
                  onChange={(event) => {
                    setResponses((current) => ({
                      ...current,
                      [question.id]: event.target.value,
                    }));
                  }}
                />
              </label>
            </div>
          </li>
        ))}
      </ol>

      <footer>
        <p role="status" aria-live="polite">{message}</p>
        <div>
          <button type="button" disabled={saving} onClick={() => save(false)}>
            {saving ? "Saving" : "Save draft"}
          </button>
          <button
            className="interview-review-button"
            type="button"
            disabled={saving}
            onClick={() => save(true)}
          >
            Save and mark fact-checked
          </button>
        </div>
      </footer>
    </section>
  );
}
