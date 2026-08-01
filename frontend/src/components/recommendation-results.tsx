import type {
  JobSearchResponse,
  RecommendationBatchResponse,
  RolePreferences,
} from "@/lib/api/job-contract";

type RecommendationResultsProps = {
  preferences: RolePreferences;
  search: JobSearchResponse;
  results: RecommendationBatchResponse;
  onRefine: () => void;
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

export function RecommendationResults({
  preferences,
  search,
  results,
  onRefine,
}: RecommendationResultsProps) {
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
          <button
            className="button results-refine"
            type="button"
            onClick={onRefine}
          >
            Refine search
          </button>
        </div>
      </div>

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
            <strong>Results are ready, with partial provider coverage.</strong>
            <span>
              {search.providers_succeeded} of {search.providers_attempted}{" "}
              sources responded. Ranking uses only verified jobs returned in
              this search.
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
                    <span className="job-source">
                      {job.source_name ?? job.source}
                    </span>
                    <h3>{job.title}</h3>
                    <p>
                      {job.company} · {job.location}
                    </p>
                  </div>
                  <div
                    className="result-score"
                    aria-label={`${score} percent match`}
                    style={{ "--score": `${score}%` } as React.CSSProperties}
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

                <div className="job-actions">
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
