# ADR 0001: Separate match assessments from ranked recommendations

- Status: Accepted
- Date: 2026-08-01

## Context

The prototype represented evaluation output with three overlapping models:
`MatchResult`, `RecommendationResult`, and `JobRecommendation`. The models used different field
names for the same concepts, mixed scoring with UI ranking, and required the facade to mutate one
model with fields copied from another.

Recommendation signal output also lived under the service layer as `SignalResult`, which caused
domain models to depend on service-layer types.

## Decision

CareerCompass uses three responsibilities:

1. `ScoreComponent` is one bounded 0-100 contribution with an explanation and optional skill
   evidence.
2. `MatchAssessment` is the versioned evaluation of one resume against one job. It owns the
   overall score, score components, skill evidence, explanation, confidence, and algorithm
   version.
3. `JobRecommendation` is the ranked user-facing record backed by a `MatchAssessment`. It may
   later own user, search, rank, saved, dismissed, and lifecycle metadata without changing the
   assessment itself.

The deterministic hybrid score remains the displayed ranking score. Optional LLM analysis may
enrich matched skills, missing skills, recruiter explanation, and suggested actions, but it does
not silently replace the deterministic score.

## Compatibility

During migration:

- `MatchResult` and `RecommendationResult` import aliases resolve to `MatchAssessment`.
- `SignalResult` resolves to `ScoreComponent`.
- Legacy input names such as `match_score`, `signal_results`, `signal_name`, and `reason` are
  accepted by validation aliases.
- `JobRecommendation` accepts its former flat constructor and adapts it into an assessment.
- Read-only compatibility properties preserve the attributes used by the Streamlit UI and
  exploratory scripts.

New production code must use the canonical model names and canonical field names.

## Consequences

- Scores are validated to remain between 0 and 100.
- Assessment algorithms carry an explicit version for reproducibility.
- Domain models no longer import recommendation service models.
- The UI remains operational without an immediate rewrite.
- Legacy aliases can be removed only after all external or exploratory callers have migrated and
  a separately approved destructive cleanup is scheduled.
