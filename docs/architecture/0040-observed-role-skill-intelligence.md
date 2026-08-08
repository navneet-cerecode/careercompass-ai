# ADR 0040: Observed-role skill intelligence

- Status: Accepted
- Date: 2026-08-09

## Context

Solara Hire has owner-scoped resume evidence and durable job-discovery, saved-job, and application
history. It does not yet have a representative labor-market dataset. Calling frequency within one
user's role history "market demand" would overstate the evidence, while ignoring that history
would waste a useful career-planning signal.

## Decision

Compute the first skill-intelligence snapshot on demand from the active reviewed resume and up to
100 distinct canonical jobs connected to the authenticated user. Tracked applications take
priority, followed by saved roles and completed authenticated searches. Duplicate jobs are
analyzed once.

Only structured `required_skills` supplied by normalized jobs count as observed requirements.
Skills are compared case-insensitively and classified as supported by resume evidence, observed but
not evidenced, or present on the resume but outside the selected role set. The response includes
role counts, short role references, source coverage, and the number of jobs without structured
skill data.

The endpoint and interface describe these values as observations from the user's Solara Hire
history. They must not present them as market-wide demand, infer missing provider data, or claim
that an unlisted resume skill is absent from the candidate's real experience.

## Consequences

- The first Phase 12 capability needs no new storage, worker, paid model call, or migration.
- Technical and non-technical skills use the same provider-neutral contract.
- Results update automatically as users search, save, apply, or upload a new resume.
- Broader labor-market benchmarking remains blocked on a representative, licensed dataset and an
  explicit methodology.
- Skill aliasing and taxonomy confidence require a later Phase 12 milestone; exact normalized names
  are the current comparison boundary.
