# ADR 0003: Separate discovery workflow from recommendation orchestration

- Status: Accepted
- Date: 2026-08-01

## Context

The prototype's only LangGraph workflow always ran job discovery followed by a dummy candidate
agent. That agent ignored the resume, evaluated only the first job, and returned a hard-coded
85% score. The Streamlit UI discarded that graph result and synchronously evaluated every job
again in its own loop.

This created two contradictory execution paths and placed batch ranking logic in the UI.

## Decision

CareerCompass uses two explicit workflow boundaries:

1. The current Streamlit search uses a discovery-only LangGraph workflow.
2. A separate resume-aware recommendation workflow is available when discovery and assessment
   genuinely need to run as one stateful graph.

`RecommendationService` is the application boundary for assessing batches, sorting by score, and
assigning recommendation ranks. Streamlit calls this service through the `CareerCompass` facade
instead of owning the ranking loop.

`CandidateEvaluationAgent` no longer contains fixtures or hard-coded scores. When the full graph
is used, it requires a resume and evaluates every discovered job through
`RecommendationService`.

## Compatibility

- `build_workflow()` remains available and resolves to the discovery-only workflow.
- `CareerCompass.recommend_job()` remains available for single-job callers.
- The existing Streamlit result model and rendering attributes are unchanged.
- The separate `candidate_evaluation_node` remains available for the real full workflow and
  legacy imports.

## Consequences

- No dummy assessment is produced in the production search path.
- Ranking has one testable application-service implementation.
- UI and graph orchestration no longer calculate contradictory results.
- The deterministic score remains the source of ranking.
- Background execution, retries, persistence, and durable LangGraph checkpoints remain later
  phases.
