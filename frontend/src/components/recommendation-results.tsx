"use client";

import { useEffect, useState, type CSSProperties } from "react";

import { ProviderAttribution } from "@/components/provider-attribution";
import { TailoringPlanAction } from "@/components/tailoring-plan-action";
import type {
  JobSearchResponse,
  RecommendationBatchResponse,
  RolePreferences,
  SavedJobListResponse,
} from "@/lib/api/job-contract";
import { getApiErrorMessage } from "@/lib/api/resume-contract";

type RecommendationResultsProps = {
  preferences: RolePreferences;
  search: JobSearchResponse;
  results: RecommendationBatchResponse;
  onRefine: () => void;
  saveAccess: "enabled" | "sign-in" | "verify-email";
};

function scoreLabel(score: number) {
  if (score >= 80) return "Strong fit";
  if (score >= 65) return "Promising";
  if (score >= 50) return "Worth a look";
  return "Stretch role";
}

function safeScore(score: number) {
  return Math.max(0, Math.min(100, Math.round(score)));
}

function providerLabel(providerName: string) {
  if (providerName === "jsearch") return "JSearch";
  if (providerName === "adzuna") return "Adzuna";
  if (providerName === "arbeitnow") return "Arbeitnow";
  if (providerName.startsWith("workday:")) {
    const company = providerName.slice("workday:".length);
    return `${company.charAt(0).toUpperCase()}${company.slice(1)} careers`;
  }
  return providerName;
}

function providerFailureReason(code: string) {
  if (code === "provider_timeout") return "timed out";
  if (code === "provider_rate_limited") return "rate limited";
  if (code === "provider_unavailable") return "temporarily unavailable";
  if (code === "provider_invalid_response") return "returned an invalid response";
  if (code === "provider_misconfigured") return "is not configured";
  return "could not be reached";
}

function isSavedJobList(value: unknown): value is SavedJobListResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "items" in value &&
    Array.isArray(value.items) &&
    value.items.every(
      (item) =>
        typeof item === "object" &&
        item !== null &&
        "job" in item &&
        typeof item.job === "object" &&
        item.job !== null &&
        "id" in item.job &&
        typeof item.job.id === "string",
    )
  );
}

export function RecommendationResults({
  preferences,
  search,
  results,
  onRefine,
  saveAccess,
}: RecommendationResultsProps) {
  const [savedJobIds, setSavedJobIds] = useState<Set<string>>(new Set());
  const [savingJobIds, setSavingJobIds] = useState<Set<string>>(new Set());
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const unavailableProviders = new Intl.ListFormat("en", {
    style: "long",
    type: "conjunction",
  }).format(
    search.provider_failures.map(
      (failure) =>
        `${providerLabel(failure.provider_name)} (${providerFailureReason(failure.code)})`,
    ),
  );

  useEffect(() => {
    if (saveAccess !== "enabled") return;
    const controller = new AbortController();
    void (async () => {
      try {
        const response = await fetch("/api/saved-jobs", {
          cache: "no-store",
          signal: controller.signal,
        });
        const payload: unknown = await response.json();
        if (response.ok && isSavedJobList(payload)) {
          setSavedJobIds(new Set(payload.items.map((item) => item.job.id)));
        }
      } catch {
        // Recommendations stay usable when saved-job state cannot be loaded.
      }
    })();
    return () => controller.abort();
  }, [saveAccess]);

  const toggleSavedJob = async (jobId: string, title: string) => {
    const isSaved = savedJobIds.has(jobId);
    setSavingJobIds((current) => new Set(current).add(jobId));
    setSaveMessage(null);
    try {
      const response = await fetch(`/api/saved-jobs/${jobId}`, {
        method: isSaved ? "DELETE" : "PUT",
        headers: isSaved ? undefined : { "Content-Type": "application/json" },
        body: isSaved ? undefined : JSON.stringify({ notes: null }),
      });
      const payload: unknown =
        response.status === 204 ? null : await response.json();
      if (!response.ok) {
        throw new Error(
          getApiErrorMessage(payload) ??
            `Solara Hire could not ${isSaved ? "remove" : "save"} this role.`,
        );
      }
      setSavedJobIds((current) => {
        const next = new Set(current);
        if (isSaved) next.delete(jobId);
        else next.add(jobId);
        return next;
      });
      setSaveMessage(
        isSaved
          ? `${title} was removed from saved roles.`
          : `${title} is now in your saved roles.`,
      );
    } catch (error) {
      setSaveMessage(
        error instanceof Error
          ? error.message
          : "Solara Hire could not update this saved role.",
      );
    } finally {
      setSavingJobIds((current) => {
        const next = new Set(current);
        next.delete(jobId);
        return next;
      });
    }
  };

  return (
    <section className="recommendation-results" aria-labelledby="matches-title">
      <div className="results-heading">
        <div>
          <span className="review-kicker">
            <span aria-hidden="true">03</span>
            Ranked opportunities
          </span>
          <h2 id="matches-title">Your clearest next moves.</h2>
          <p>
            {results.recommendations.length} roles ranked for{" "}
            <strong>{preferences.role}</strong> in {preferences.location}.
            Scores compare your reviewed evidence with each job.
          </p>
        </div>
        <div className="results-heading-actions">
          <span className="results-assurance">Review-first · No auto-apply</span>
          {saveAccess === "enabled" && (
            <a className="results-saved-link" href="/saved">
              Saved roles
              <span>{savedJobIds.size}</span>
            </a>
          )}
          <button
            className="button results-refine"
            type="button"
            onClick={onRefine}
          >
            Refine search
          </button>
        </div>
      </div>

      <p className="save-feedback" role="status" aria-live="polite">
        {saveMessage}
      </p>

      <div className="results-overview" aria-label="Search summary">
        <div>
          <strong>{results.recommendations.length}</strong>
          <span>ranked roles</span>
        </div>
        <div>
          <strong>
            {search.providers_succeeded}/{search.providers_attempted}
          </strong>
          <span>sources reached</span>
        </div>
        <div>
          <strong>{preferences.location}</strong>
          <span>search area</span>
        </div>
        <div>
          <strong>
            {preferences.datePosted === "all"
              ? "Any time"
              : `Past ${preferences.datePosted}`}
          </strong>
          <span>freshness</span>
        </div>
      </div>

      {search.status === "partial" && (
        <div className="provider-notice" role="status">
          <span aria-hidden="true">i</span>
          <div>
            <strong>
              Results are ready. {" "}
              {search.provider_failures.length === 1
                ? "One source needs another pass."
                : `${search.provider_failures.length} sources need another pass.`}
            </strong>
            <span>
              {unavailableProviders || "A job source"} could not be used for
              this search. Safe transient failures were retried. These rankings
              use only the verified jobs returned by the other{" "}
              {search.providers_succeeded} source
              {search.providers_succeeded === 1 ? "" : "s"}.
            </span>
          </div>
        </div>
      )}

      <div className="recommendation-list">
        {results.recommendations.map((recommendation, index) => {
          const assessment = recommendation.assessment;
          const job = assessment.job;
          const score = safeScore(assessment.score);
          const rank = recommendation.rank ?? index + 1;
          const hasEvidence =
            assessment.matched_skills.length > 0 ||
            assessment.missing_skills.length > 0;

          return (
            <article className="recommendation-card" key={recommendation.id}>
              <div className="recommendation-rank">
                <span>#{String(rank).padStart(2, "0")}</span>
                <small>{scoreLabel(score)}</small>
              </div>

              <div className="recommendation-body">
                <div className="job-heading">
                  <div>
                    <ProviderAttribution {...job} />
                    <h3>{job.title}</h3>
                    <p>
                      {job.company} · {job.location}
                    </p>
                  </div>
                  <div
                    className="result-score"
                    aria-label={`${score} percent match`}
                    style={{ "--score": `${score}%` } as CSSProperties}
                  >
                    <strong>{score}</strong>
                    <span>match</span>
                  </div>
                </div>

                <div className="job-facts">
                  <span>{job.employment_type}</span>
                  <span>{job.experience_level}</span>
                  <span>Model {assessment.algorithm_version}</span>
                </div>

                {assessment.recruiter_summary && (
                  <p className="recruiter-summary">
                    {assessment.recruiter_summary}
                  </p>
                )}

                {hasEvidence && (
                  <div className="evidence-columns">
                    {assessment.matched_skills.length > 0 && (
                      <div>
                        <span className="micro-label">Evidence that matches</span>
                        <div className="evidence-chips matched">
                          {assessment.matched_skills.map((skill) => (
                            <span key={skill.name}>{skill.name}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {assessment.missing_skills.length > 0 && (
                      <div>
                        <span className="micro-label">Growth edge</span>
                        <div className="evidence-chips missing">
                          {assessment.missing_skills.map((skill) => (
                            <span key={skill.name}>{skill.name}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <details className="match-details">
                  <summary>Why this role ranks here</summary>
                  <div className="component-list">
                    {assessment.components.map((component) => {
                      const componentScore = safeScore(component.score);
                      return (
                        <div className="component-row" key={component.name}>
                          <div>
                            <strong>{component.name}</strong>
                            <span>{componentScore}</span>
                          </div>
                          <div className="component-track">
                            <span style={{ width: `${componentScore}%` }} />
                          </div>
                          <p>{component.explanation}</p>
                        </div>
                      );
                    })}
                  </div>

                  {assessment.recommendations.length > 0 && (
                    <div className="next-actions">
                      <span className="micro-label">Before you apply</span>
                      <ul>
                        {assessment.recommendations.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </details>

                <TailoringPlanAction
                  jobId={job.id}
                  jobTitle={job.title}
                  access={saveAccess}
                />

                <div className="job-actions">
                  {saveAccess === "enabled" ? (
                    <button
                      className={`button save-job-button ${
                        savedJobIds.has(job.id) ? "is-saved" : ""
                      }`}
                      type="button"
                      aria-pressed={savedJobIds.has(job.id)}
                      aria-label={`${
                        savedJobIds.has(job.id) ? "Remove" : "Save"
                      } ${job.title}`}
                      disabled={savingJobIds.has(job.id)}
                      onClick={() => toggleSavedJob(job.id, job.title)}
                    >
                      <span aria-hidden="true">
                        {savedJobIds.has(job.id) ? "✓" : "+"}
                      </span>
                      {savingJobIds.has(job.id)
                        ? "Updating"
                        : savedJobIds.has(job.id)
                          ? "Saved"
                          : "Save role"}
                    </button>
                  ) : saveAccess === "sign-in" ? (
                    <a
                      className="button save-job-button"
                      href="/auth/login"
                    >
                      <span aria-hidden="true">+</span>
                      Sign in to save
                    </a>
                  ) : (
                    <button
                      className="button save-job-button"
                      type="button"
                      disabled
                      title="Verify your email, then sign out and back in."
                    >
                      Verify email to save
                    </button>
                  )}
                  <a
                    className="button apply-button"
                    href={job.url}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={`Review ${job.title} at ${job.company} (opens in a new tab)`}
                  >
                    Review job
                    <span aria-hidden="true">↗</span>
                  </a>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
