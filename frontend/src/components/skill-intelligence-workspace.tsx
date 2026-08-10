"use client";

import { useEffect, useMemo, useState } from "react";

import type {
  SkillIntelligenceItemResponse,
  SkillIntelligenceResponse,
} from "@/lib/api/job-contract";
import { getApiErrorMessage } from "@/lib/api/resume-contract";

type IntelligenceState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; snapshot: SkillIntelligenceResponse };

type Filter = "all" | "supported" | "develop" | "resume_only";

const FILTERS: { value: Filter; label: string }[] = [
  { value: "all", label: "All evidence" },
  { value: "supported", label: "Role + resume" },
  { value: "develop", label: "Develop" },
  { value: "resume_only", label: "Resume only" },
];

function isSnapshot(value: unknown): value is SkillIntelligenceResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "skills" in value &&
    Array.isArray(value.skills) &&
    "roles_analyzed" in value &&
    typeof value.roles_analyzed === "number"
  );
}

function stateLabel(item: SkillIntelligenceItemResponse) {
  if (item.status === "supported") return "Evidence aligns with role set";
  if (item.status === "develop") return "Build or verify evidence";
  return "Not observed in this role set";
}

function confidenceLabel(item: SkillIntelligenceItemResponse) {
  if (item.match_confidence === "exact") return "Exact wording";
  if (item.match_confidence === "curated_high") {
    return "Curated alias · high confidence";
  }
  return null;
}

export function SkillIntelligenceWorkspace() {
  const [state, setState] = useState<IntelligenceState>({ status: "loading" });
  const [filter, setFilter] = useState<Filter>("all");

  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      try {
        const response = await fetch("/api/skill-intelligence", {
          cache: "no-store",
          signal: controller.signal,
        });
        const payload: unknown = await response.json();
        if (!response.ok || !isSnapshot(payload)) {
          throw new Error(
            getApiErrorMessage(payload) ??
              "Solara Hire could not load your skill intelligence.",
          );
        }
        setState({ status: "ready", snapshot: payload });
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "Solara Hire could not load your skill intelligence.",
        });
      }
    })();
    return () => controller.abort();
  }, []);

  const skills = useMemo(() => {
    if (state.status !== "ready") return [];
    return state.snapshot.skills.filter(
      (skill) => filter === "all" || skill.status === filter,
    );
  }, [filter, state]);

  if (state.status === "loading") {
    return (
      <main id="main-content" className="intelligence-main">
        <p className="intelligence-state">Comparing your evidence with your role history…</p>
      </main>
    );
  }

  if (state.status === "error") {
    return (
      <main id="main-content" className="intelligence-main">
        <section className="intelligence-state">
          <h1>Your evidence is still intact.</h1>
          <p>{state.message}</p>
          <button type="button" onClick={() => window.location.reload()}>Try again</button>
        </section>
      </main>
    );
  }

  const { snapshot } = state;
  if (!snapshot.resume_id) {
    return (
      <main id="main-content" className="intelligence-main">
        <section className="intelligence-state">
          <h1>Start with a reviewed resume.</h1>
          <p>
            Skill intelligence needs resume evidence before it can compare your experience with
            roles you choose.
          </p>
          <a className="button" href="/workspace">Upload and review a resume</a>
        </section>
      </main>
    );
  }

  if (snapshot.roles_analyzed === 0) {
    return (
      <main id="main-content" className="intelligence-main">
        <section className="intelligence-state">
          <h1>Choose a few roles to create your comparison.</h1>
          <p>
            Search, save, or track roles in Solara Hire. This page will compare their stated
            skills with your reviewed resume.
          </p>
          <a className="button" href="/workspace">Discover roles</a>
        </section>
      </main>
    );
  }

  const hasObservedSkillData = snapshot.roles_with_skill_data > 0;

  return (
    <main id="main-content" className="intelligence-main">
      <section className="intelligence-opening" aria-labelledby="intelligence-title">
        <div>
          <h1 id="intelligence-title">
            {hasObservedSkillData
              ? "See what your chosen roles keep asking for."
              : "Your resume is ready. The role data is not—yet."}
          </h1>
          {hasObservedSkillData ? (
            <p>
              Compare your reviewed resume with the jobs in your own Solara Hire history. Every
              count below comes from those roles—not from the wider labor market.
            </p>
          ) : (
            <p>
              We found {snapshot.roles_analyzed} roles in your history, but none included
              structured skill fields. Your resume evidence stays visible below without claiming
              those roles asked for it.
            </p>
          )}
        </div>
        <aside aria-label="Evidence boundary">
          <strong>What this measures</strong>
          <p>
            {snapshot.roles_with_skill_data} of {snapshot.roles_analyzed} roles included explicit
            skill data. {snapshot.roles_without_skill_data} did not and are kept visible as a
            coverage limitation.
          </p>
        </aside>
      </section>

      <section className="intelligence-sources" aria-label="Roles included in this comparison">
        <p>
          <strong>{snapshot.roles_analyzed} distinct roles analyzed</strong>
          <span>{snapshot.search_history_roles} from searches</span>
          <span>{snapshot.saved_roles} saved</span>
          <span>{snapshot.application_roles} tracked applications</span>
        </p>
        <small>A role can appear in more than one source. It is analyzed only once.</small>
      </section>

      {snapshot.skills.length === 0 ? (
        <section className="intelligence-state intelligence-state-inline">
          <h2>These roles did not include structured skill data.</h2>
          <p>
            Solara Hire will not infer requirements that providers did not supply. Try another
            search or review the original job pages.
          </p>
        </section>
      ) : (
        <section className="intelligence-matrix" aria-labelledby="matrix-title">
          <header>
            <div>
              <h2 id="matrix-title">
                {hasObservedSkillData ? "Evidence comparison" : "Resume evidence inventory"}
              </h2>
              <p>
                {hasObservedSkillData
                  ? "Use repeated requirements as a priority signal, not proof of market-wide demand."
                  : "These skills come from your reviewed resume; the current role set adds no structured demand evidence."}
              </p>
            </div>
            <div className="intelligence-filters" aria-label="Filter skill evidence">
              {FILTERS.map((option) => (
                <button
                  type="button"
                  key={option.value}
                  aria-pressed={filter === option.value}
                  onClick={() => setFilter(option.value)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </header>

          {skills.length === 0 ? (
            <p className="intelligence-filter-empty">No skills match this evidence filter.</p>
          ) : (
            <div className="intelligence-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Skill</th>
                    <th scope="col">Resume</th>
                    <th scope="col">Observed roles</th>
                    <th scope="col">Where it appeared</th>
                    <th scope="col">Interpretation</th>
                  </tr>
                </thead>
                <tbody key={filter}>
                  {skills.map((skill) => (
                    <tr key={`${skill.status}-${skill.name}`} data-status={skill.status}>
                      <th scope="row">
                        <strong>{skill.name}</strong>
                        <span>{skill.category ?? "Uncategorized"}</span>
                      </th>
                      <td data-label="Resume">
                        {skill.resume_evidenced ? "Evidenced" : "Not found"}
                      </td>
                      <td data-label="Observed roles">
                        <strong>{skill.observed_role_count}</strong>
                        <span>of {snapshot.roles_analyzed}</span>
                      </td>
                      <td data-label="Where it appeared">
                        {skill.observed_roles.length > 0 ? (
                          <ul>
                            {skill.observed_roles.map((role) => (
                              <li key={role.job_id}>
                                {role.title} <span>at {role.company}</span>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <span>Outside this role set</span>
                        )}
                      </td>
                      <td data-label="Interpretation">
                        <span className="intelligence-status">{stateLabel(skill)}</span>
                        {confidenceLabel(skill) ? (
                          <span className="intelligence-confidence">
                            {confidenceLabel(skill)}
                          </span>
                        ) : null}
                        {skill.match_confidence === "curated_high" ? (
                          <span className="intelligence-match-note">
                            Matched terms: {skill.matched_terms.join(" ↔ ")}
                          </span>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
