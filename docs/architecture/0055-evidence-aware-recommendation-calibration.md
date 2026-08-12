# ADR 0055: Evidence-aware recommendation calibration

- Status: Accepted
- Date: 2026-08-13

## Context

The hybrid recommendation engine previously assigned a neutral skill score of 50 when a provider
supplied no structured requirements. Users could not distinguish unavailable evidence from a real
50-percent skill match, and the neutral value diluted the semantic signal. Assessments also lacked
a consistent evidence-coverage explanation and could contain duplicate or contradictory skills.

## Decision

Keep the existing deterministic skill and semantic signals, but mark whether each component has
evidence. Exclude unavailable components from score fusion and report weighted evidence coverage
as assessment confidence. Label this behavior `hybrid-v2` so persisted history remains auditable.

Use the curated cross-industry skill aliases during comparison. Deduplicate aggregate skill
evidence and let matched evidence take precedence over a contradictory missing entry. Generate
short deterministic summaries and review-first actions from the assessment evidence. Never infer
that an absent structured requirement is a candidate weakness, and never instruct users to add an
unverified skill to application materials.

Expose unavailable components as `Not scored` in the workspace rather than rendering a misleading
progress bar. Keep the component explanation, evidence percentage, and algorithm version visible.

## Consequences

- A role without structured skills is ranked by semantic similarity alone instead of a fabricated
  neutral skill score.
- Users can see how much configured scoring weight had evidence for each recommendation.
- Technical and non-technical skill aliases share the same deterministic matching boundary.
- Historical `hybrid-v1` assessments remain readable while new assessments are distinguishable.
- Future calibration should be evaluated against representative labeled outcomes before changing
  weights or interpreting scores as hiring probabilities.
