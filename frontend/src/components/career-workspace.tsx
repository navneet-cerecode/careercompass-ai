"use client";

import { useEffect, useRef, useState } from "react";

import { RecommendationResults } from "@/components/recommendation-results";
import { ResumeOnboarding } from "@/components/resume-onboarding";
import { RolePreferencesForm } from "@/components/role-preferences-form";
import {
  buildJobSearchRequest,
  buildRecommendationRequest,
  type JobSearchResponse,
  type JobSearchTaskCreatedResponse,
  type JobSearchTaskResponse,
  type RecommendationBatchResponse,
  type RolePreferences,
} from "@/lib/api/job-contract";
import {
  getApiErrorMessage,
  type ParsedResumeResponse,
} from "@/lib/api/resume-contract";

type WorkflowStep = "profile" | "preferences" | "matches";

type MatchState =
  | { status: "idle" }
  | { status: "searching"; phase: "queued" | "running" }
  | { status: "ranking"; jobsFound: number }
  | { status: "error"; message: string }
  | {
      status: "success";
      search: JobSearchResponse;
      results: RecommendationBatchResponse;
    };

const DEFAULT_PREFERENCES: RolePreferences = {
  role: "",
  location: "India",
  country: "IN",
  remoteOnly: false,
  employmentTypes: ["Full Time"],
  datePosted: "month",
};

const stepNames = ["Profile", "Preferences", "Matches"] as const;

const stepCopy: Record<
  WorkflowStep,
  { eyebrow: string; title: string; emphasis: string; description: string }
> = {
  profile: {
    eyebrow: "Your private workspace",
    title: "Let's map what",
    emphasis: "you already know.",
    description:
      "Upload your current resume. CareerCompass will extract a profile for you to inspect before it scores a single opportunity.",
  },
  preferences: {
    eyebrow: "A focused search",
    title: "Point the compass",
    emphasis: "toward your next move.",
    description:
      "Choose the role, location, and working style that matter now. These preferences shape discovery, not your underlying profile.",
  },
  matches: {
    eyebrow: "Explainable recommendations",
    title: "See the fit.",
    emphasis: "Keep the judgment.",
    description:
      "Each rank separates evidence, missing skills, and practical next steps so you can decide where your energy belongs.",
  },
};

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function isJobSearchResponse(value: unknown): value is JobSearchResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "status" in value &&
    ["complete", "partial", "failed"].includes(String(value.status)) &&
    "jobs" in value &&
    Array.isArray(value.jobs) &&
    "providers_attempted" in value &&
    typeof value.providers_attempted === "number" &&
    "providers_succeeded" in value &&
    typeof value.providers_succeeded === "number"
  );
}

function isRecommendationResponse(
  value: unknown,
): value is RecommendationBatchResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "recommendations" in value &&
    Array.isArray(value.recommendations)
  );
}

function isTaskCreatedResponse(
  value: unknown,
): value is JobSearchTaskCreatedResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "task_id" in value &&
    typeof value.task_id === "string" &&
    "access_token" in value &&
    typeof value.access_token === "string" &&
    "status" in value
  );
}

function isTaskResponse(value: unknown): value is JobSearchTaskResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "task_id" in value &&
    typeof value.task_id === "string" &&
    "status" in value &&
    ["queued", "running", "succeeded", "failed", "cancelled"].includes(
      String(value.status),
    )
  );
}

function hasErrorCode(value: unknown, code: string) {
  return (
    typeof value === "object" &&
    value !== null &&
    "code" in value &&
    value.code === code
  );
}

function waitForPoll(signal: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    const timer = window.setTimeout(resolve, 900);
    signal.addEventListener(
      "abort",
      () => {
        window.clearTimeout(timer);
        reject(new DOMException("Search cancelled.", "AbortError"));
      },
      { once: true },
    );
  });
}

export function CareerWorkspace() {
  const [step, setStep] = useState<WorkflowStep>("profile");
  const [profile, setProfile] = useState<ParsedResumeResponse | null>(null);
  const [preferences, setPreferences] =
    useState<RolePreferences>(DEFAULT_PREFERENCES);
  const [matchState, setMatchState] = useState<MatchState>({ status: "idle" });
  const titleRef = useRef<HTMLHeadingElement>(null);
  const previousStepRef = useRef<WorkflowStep>("profile");
  const searchControllerRef = useRef<AbortController | null>(null);

  const copy = stepCopy[step];
  const currentStep = step === "profile" ? 1 : step === "preferences" ? 2 : 3;
  const isMatching =
    matchState.status === "searching" || matchState.status === "ranking";

  useEffect(() => {
    if (previousStepRef.current !== step) {
      titleRef.current?.focus();
      previousStepRef.current = step;
    }
  }, [step]);

  useEffect(
    () => () => {
      searchControllerRef.current?.abort();
    },
    [],
  );

  const handleProfileContinue = (result: ParsedResumeResponse) => {
    setProfile(result);
    setStep("preferences");
    setMatchState({ status: "idle" });
  };

  const handleMatch = async (nextPreferences: RolePreferences) => {
    if (!profile) {
      setStep("profile");
      return;
    }

    setPreferences(nextPreferences);
    setStep("matches");
    searchControllerRef.current?.abort();
    const controller = new AbortController();
    searchControllerRef.current = controller;
    setMatchState({ status: "searching", phase: "queued" });

    try {
      const requestBody = JSON.stringify(buildJobSearchRequest(nextPreferences));
      const taskResponse = await fetch("/api/jobs/search-tasks", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": crypto.randomUUID(),
        },
        body: requestBody,
        signal: controller.signal,
      });
      const taskPayload = await readJson(taskResponse);
      let search: JobSearchResponse;

      if (!taskResponse.ok && hasErrorCode(taskPayload, "worker_not_configured")) {
        const fallbackResponse = await fetch("/api/jobs/search", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: requestBody,
          signal: controller.signal,
        });
        const fallbackPayload = await readJson(fallbackResponse);
        if (!fallbackResponse.ok || !isJobSearchResponse(fallbackPayload)) {
          throw new Error(
            getApiErrorMessage(fallbackPayload) ??
              "CareerCompass could not search jobs with these preferences.",
          );
        }
        search = fallbackPayload;
      } else {
        if (!taskResponse.ok || !isTaskCreatedResponse(taskPayload)) {
          throw new Error(
            getApiErrorMessage(taskPayload) ??
              "CareerCompass could not start this job search.",
          );
        }

        const deadline = Date.now() + 2 * 60 * 1000;
        let completedSearch: JobSearchResponse | null = null;
        while (Date.now() < deadline) {
          await waitForPoll(controller.signal);
          const pollResponse = await fetch(
            `/api/jobs/search-tasks/${taskPayload.task_id}`,
            {
              headers: { "X-Task-Token": taskPayload.access_token },
              cache: "no-store",
              signal: controller.signal,
            },
          );
          const pollPayload = await readJson(pollResponse);
          if (!pollResponse.ok || !isTaskResponse(pollPayload)) {
            throw new Error(
              getApiErrorMessage(pollPayload) ??
                "CareerCompass lost contact with this search.",
            );
          }
          if (pollPayload.status === "running") {
            setMatchState({ status: "searching", phase: "running" });
          }
          if (
            pollPayload.status === "failed" ||
            pollPayload.status === "cancelled"
          ) {
            throw new Error(
              "The background search could not finish. Please try again.",
            );
          }
          if (pollPayload.status === "succeeded") {
            if (!isJobSearchResponse(pollPayload.result)) {
              throw new Error("Job search completed without a usable result.");
            }
            completedSearch = pollPayload.result;
            break;
          }
        }
        if (!completedSearch) {
          throw new Error(
            "This search is taking longer than expected. Please try again.",
          );
        }
        search = completedSearch;
      }

      if (search.jobs.length === 0) {
        setMatchState({
          status: "error",
          message:
            search.status === "failed"
              ? "Job providers did not return a usable result. Try again shortly or broaden the search."
              : "No verified jobs matched this search. Try a broader role, location, or date range.",
        });
        return;
      }

      setMatchState({ status: "ranking", jobsFound: search.jobs.length });
      const recommendationResponse = await fetch("/api/recommendations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          buildRecommendationRequest(profile, search.jobs),
        ),
        signal: controller.signal,
      });
      const recommendationPayload = await readJson(recommendationResponse);

      if (!recommendationResponse.ok) {
        throw new Error(
          getApiErrorMessage(recommendationPayload) ??
            "CareerCompass could not rank these jobs right now.",
        );
      }

      if (!isRecommendationResponse(recommendationPayload)) {
        throw new Error("Job ranking returned an unexpected response.");
      }

      if (recommendationPayload.recommendations.length === 0) {
        throw new Error(
          "No ranked recommendations were returned. Refine the search and try again.",
        );
      }

      setMatchState({
        status: "success",
        search,
        results: recommendationPayload,
      });
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      setMatchState({
        status: "error",
        message:
          error instanceof Error
            ? error.message
            : "CareerCompass could not complete this search.",
      });
    }
  };

  return (
    <main
      id="main-content"
      className={`workspace-main workspace-main-${step}`}
    >
      <section className="workspace-intro" aria-labelledby="workspace-title">
        <div
          className="workspace-progress"
          aria-label="Onboarding progress"
          role="list"
        >
          {[1, 2, 3].map((number, index) => (
            <span
              key={number}
              className="progress-fragment"
              role="listitem"
              aria-current={number === currentStep ? "step" : undefined}
              aria-label={`${stepNames[index]}: ${
                number === currentStep
                  ? "current step"
                  : number < currentStep
                    ? "complete"
                    : "not started"
              }`}
            >
              <span
                aria-hidden="true"
                className={
                  number === currentStep
                    ? "step-number is-current"
                    : number < currentStep
                      ? "step-number is-complete"
                      : "step-number"
                }
              >
                {number < currentStep ? "✓" : `0${number}`}
              </span>
              <span className="step-name" aria-hidden="true">
                {stepNames[index]}
              </span>
              {number < 3 && <span className="progress-line" aria-hidden="true" />}
            </span>
          ))}
        </div>

        <span className="micro-label">{copy.eyebrow}</span>
        <h1 id="workspace-title" ref={titleRef} tabIndex={-1}>
          {copy.title}{" "}
          <span>{copy.emphasis}</span>
        </h1>
        <p>{copy.description}</p>

        <div className="workspace-promises">
          <div>
            <span aria-hidden="true">01</span>
            <strong>No silent rewriting</strong>
          </div>
          <div>
            <span aria-hidden="true">02</span>
            <strong>Every score has evidence</strong>
          </div>
          <div>
            <span aria-hidden="true">03</span>
            <strong>You choose when to apply</strong>
          </div>
        </div>
      </section>

      <div
        className={`workspace-panel workspace-panel-${step}`}
        role="region"
        aria-label={`${stepNames[currentStep - 1]} workspace`}
        aria-busy={isMatching}
      >
        {step === "profile" && (
          <ResumeOnboarding
            initialResult={profile ?? undefined}
            onContinue={handleProfileContinue}
          />
        )}

        {step === "preferences" && (
          <RolePreferencesForm
            initialPreferences={preferences}
            onBack={() => setStep("profile")}
            onSubmit={handleMatch}
          />
        )}

        {step === "matches" &&
          (matchState.status === "success" ? (
            <RecommendationResults
              preferences={preferences}
              search={matchState.search}
              results={matchState.results}
              onRefine={() => setStep("preferences")}
            />
          ) : (
            <section
              className="matching-state"
              aria-live="polite"
              aria-atomic="true"
            >
              {matchState.status === "error" ? (
                <>
                  <span className="matching-symbol is-error" aria-hidden="true">
                    !
                  </span>
                  <span className="micro-label">Search needs another pass</span>
                  <h2>We could not finish this match set.</h2>
                  <p>{matchState.message}</p>
                  <div className="matching-actions">
                    <button
                      className="button button-quiet"
                      type="button"
                      onClick={() => setStep("preferences")}
                    >
                      Refine preferences
                    </button>
                    <button
                      className="button match-button"
                      type="button"
                      onClick={() => handleMatch(preferences)}
                    >
                      Try again
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <span className="matching-symbol" aria-hidden="true">
                    <span />
                  </span>
                  <span className="micro-label">Building your match set</span>
                  <h2>
                    {matchState.status === "ranking"
                      ? `Ranking ${matchState.jobsFound} verified jobs.`
                      : matchState.status === "searching" &&
                          matchState.phase === "queued"
                        ? "Your verified search is queued."
                        : "Searching across verified sources."}
                  </h2>
                  <p>
                    {matchState.status === "ranking"
                      ? "Comparing role requirements with the evidence you reviewed."
                      : matchState.status === "searching" &&
                          matchState.phase === "queued"
                        ? "A worker will begin discovery shortly. You can keep this page open."
                        : "Normalizing results and merging duplicate opportunities before scoring."}
                  </p>
                  <div className="matching-steps">
                    <span className="is-active">Discover</span>
                    <span
                      className={
                        matchState.status === "ranking" ? "is-active" : ""
                      }
                    >
                      Normalize
                    </span>
                    <span
                      className={
                        matchState.status === "ranking" ? "is-active" : ""
                      }
                    >
                      Rank
                    </span>
                  </div>
                </>
              )}
            </section>
          ))}
      </div>
    </main>
  );
}
