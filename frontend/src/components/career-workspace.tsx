"use client";

import { useState } from "react";

import { RecommendationResults } from "@/components/recommendation-results";
import { ResumeOnboarding } from "@/components/resume-onboarding";
import { RolePreferencesForm } from "@/components/role-preferences-form";
import {
  buildJobSearchRequest,
  buildRecommendationRequest,
  type JobSearchResponse,
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
  | { status: "searching" }
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

export function CareerWorkspace() {
  const [step, setStep] = useState<WorkflowStep>("profile");
  const [profile, setProfile] = useState<ParsedResumeResponse | null>(null);
  const [preferences, setPreferences] =
    useState<RolePreferences>(DEFAULT_PREFERENCES);
  const [matchState, setMatchState] = useState<MatchState>({ status: "idle" });

  const copy = stepCopy[step];
  const currentStep = step === "profile" ? 1 : step === "preferences" ? 2 : 3;

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
    setMatchState({ status: "searching" });

    try {
      const searchResponse = await fetch("/api/jobs/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildJobSearchRequest(nextPreferences)),
      });
      const searchPayload = await readJson(searchResponse);

      if (!searchResponse.ok) {
        throw new Error(
          getApiErrorMessage(searchPayload) ??
            "CareerCompass could not search jobs with these preferences.",
        );
      }

      if (!isJobSearchResponse(searchPayload)) {
        throw new Error("Job search returned an unexpected response.");
      }

      const search = searchPayload;
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
    <main id="main-content" className="workspace-main">
      <section className="workspace-intro" aria-labelledby="workspace-title">
        <div className="workspace-progress" aria-label="Onboarding progress">
          {[1, 2, 3].map((number, index) => (
            <span key={number} className="progress-fragment">
              <span
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
              <span className="step-name">
                {["Profile", "Preferences", "Matches"][index]}
              </span>
              {number < 3 && <span className="progress-line" aria-hidden="true" />}
            </span>
          ))}
        </div>

        <span className="micro-label">{copy.eyebrow}</span>
        <h1 id="workspace-title">
          {copy.title}
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

      <div className={`workspace-panel workspace-panel-${step}`}>
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
            <section className="matching-state" aria-live="polite">
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
                      : "Searching across verified sources."}
                  </h2>
                  <p>
                    {matchState.status === "ranking"
                      ? "Comparing role requirements with the evidence you reviewed."
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
