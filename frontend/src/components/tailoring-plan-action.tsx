"use client";

import { useState } from "react";

import { TailoredResumeWorkspace } from "@/components/tailored-resume-workspace";
import { CoverLetterWorkspace } from "@/components/cover-letter-workspace";
import type { TailoringPlanResponse } from "@/lib/api/job-contract";
import { getApiErrorMessage } from "@/lib/api/resume-contract";

type TailoringPlanActionProps = {
  jobId: string;
  jobTitle: string;
  access: "enabled" | "sign-in" | "verify-email";
};

type PlanState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; plan: TailoringPlanResponse; open: boolean }
  | { status: "error"; message: string; upgradeRequired: boolean };

function isTailoringPlan(value: unknown): value is TailoringPlanResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof value.id === "string" &&
    "experience" in value &&
    Array.isArray(value.experience) &&
    "projects" in value &&
    Array.isArray(value.projects) &&
    "user_review_required" in value &&
    value.user_review_required === true
  );
}

export function TailoringPlanAction({
  jobId,
  jobTitle,
  access,
}: TailoringPlanActionProps) {
  const [state, setState] = useState<PlanState>({ status: "idle" });

  if (access === "sign-in") {
    return (
      <a className="button tailor-plan-button" href="/auth/login">
        Sign in to tailor
      </a>
    );
  }

  if (access === "verify-email") {
    return (
      <button
        className="button tailor-plan-button"
        type="button"
        disabled
        title="Verify your email, then sign out and back in."
      >
        Verify email to tailor
      </button>
    );
  }

  const createPlan = async () => {
    if (state.status === "success") {
      setState({ ...state, open: !state.open });
      return;
    }

    setState({ status: "loading" });
    try {
      const response = await fetch("/api/tailoring-plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId }),
      });
      const payload: unknown = await response.json();
      if (!response.ok || !isTailoringPlan(payload)) {
        throw Object.assign(
          new Error(
            getApiErrorMessage(payload) ??
              "Solara Hire could not prepare this factual plan.",
          ),
          { upgradeRequired: response.status === 403 },
        );
      }
      setState({ status: "success", plan: payload, open: true });
    } catch (error) {
      setState({
        status: "error",
        message:
          error instanceof Error
            ? error.message
            : "Solara Hire could not prepare this factual plan.",
        upgradeRequired:
          typeof error === "object" &&
          error !== null &&
          "upgradeRequired" in error &&
          error.upgradeRequired === true,
      });
    }
  };

  const plan = state.status === "success" ? state.plan : null;

  return (
    <div className="tailoring-action">
      <button
        className="button tailor-plan-button"
        type="button"
        disabled={state.status === "loading"}
        aria-expanded={state.status === "success" ? state.open : false}
        onClick={createPlan}
      >
        {state.status === "loading"
          ? "Preparing evidence"
          : state.status === "success" && state.open
            ? "Hide factual plan"
            : state.status === "success"
              ? "Review factual plan"
              : "Tailor with my facts"}
      </button>

      {state.status === "error" && (
        <div className="tailoring-error" role="alert">
          <span>{state.message}</span>
          {state.upgradeRequired && (
            <a href="/settings/billing">Review plan access</a>
          )}
          <button type="button" onClick={() => setState({ status: "idle" })}>
            Dismiss
          </button>
        </div>
      )}

      {plan && state.status === "success" && state.open && (
        <section
          className="tailoring-review"
          aria-label={`Factual tailoring plan for ${jobTitle}`}
        >
          <header>
            <div>
              <span className="micro-label">Factual ordering plan</span>
              <h4>Lead with what this role needs.</h4>
            </div>
            <span className="review-required">Review required</span>
          </header>

          <p className="tailoring-assurance">
            Nothing new was written. Solara Hire only reordered evidence from
            your uploaded resume. Missing skills remain clearly separate.
          </p>

          <div className="tailoring-skill-grid">
            <div>
              <span className="micro-label">Evidence found</span>
              <div className="evidence-chips matched">
                {plan.matched_skills.length > 0 ? (
                  plan.matched_skills.map((skill) => (
                    <span key={skill.name}>{skill.name}</span>
                  ))
                ) : (
                  <span>No direct skill match found</span>
                )}
              </div>
            </div>
            <div>
              <span className="micro-label">Do not claim yet</span>
              <div className="evidence-chips missing">
                {plan.missing_skills.length > 0 ? (
                  plan.missing_skills.map((skill) => (
                    <span key={skill.name}>{skill.name}</span>
                  ))
                ) : (
                  <span>No listed gaps</span>
                )}
              </div>
            </div>
          </div>

          {(plan.experience.length > 0 || plan.projects.length > 0) && (
            <div className="tailoring-sections">
              {plan.experience.length > 0 && (
                <div>
                  <span className="micro-label">Experience order</span>
                  <ol>
                    {plan.experience.map((item, index) => (
                      <li key={`${index}-${item}`}>{item}</li>
                    ))}
                  </ol>
                </div>
              )}
              {plan.projects.length > 0 && (
                <div>
                  <span className="micro-label">Project order</span>
                  <ol>
                    {plan.projects.map((item, index) => (
                      <li key={`${index}-${item}`}>{item}</li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          )}

          {plan.evidence.length > 0 && (
            <div className="tailoring-evidence-ledger">
              <span className="micro-label">Why this evidence moved up</span>
              {plan.evidence.map((item) => (
                <div key={`${item.section}-${item.source_index}`}>
                  <p>{item.source_text}</p>
                  <span>
                    {item.matched_terms.length > 0
                      ? `Matches: ${item.matched_terms.join(", ")}`
                      : "Original resume evidence"}
                  </span>
                </div>
              ))}
            </div>
          )}

          <section className="application-document-workspace" aria-label="Application documents">
            <header>
              <h5>Prepare your application documents.</h5>
              <p>Both documents keep their own review history and require your approval.</p>
            </header>
            <div className="application-document-options">
              <article>
                <div>
                  <strong>Tailored résumé</strong>
                  <span>Reorder verified evidence for this role.</span>
                </div>
                <TailoredResumeWorkspace planId={plan.id} jobTitle={jobTitle} />
              </article>
              <article>
                <div>
                  <strong>Cover letter</strong>
                  <span>Draft, edit, verify, and export a job-specific letter.</span>
                </div>
                <CoverLetterWorkspace planId={plan.id} jobTitle={jobTitle} />
              </article>
            </div>
          </section>

          <footer>
            <span>Plan {plan.algorithm_version}</span>
            <strong>Next: inspect every line before exporting.</strong>
          </footer>
        </section>
      )}
    </div>
  );
}
