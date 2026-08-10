# ADR 0043: Evidence-first development priorities

- Status: Accepted
- Date: 2026-08-10

## Context

The skill-intelligence comparison already identifies requirements observed in a user's selected
roles but not found in their reviewed resume. Turning that list into a plan must remain useful
without implying that the user lacks a capability or that a personal role sample represents the
labor market.

## Decision

Build the first development plan in the frontend from the existing skill-intelligence response.
Include up to five `develop` items, ordered by observed-role count and then skill name. Each item
shows its evidence count and available role references.

Every priority uses the same review-first action: check existing work for specific, truthful
evidence; only choose a learning or practice step when that evidence does not exist. The plan does
not recommend providers, invent experience, mutate the resume, or introduce a separate score.

## Consequences

- The plan updates automatically with the existing owner-scoped snapshot.
- No database migration, background task, paid model call, or API change is required.
- Users retain the distinction between missing resume evidence and a missing real-world skill.
- Personalized learning resources can be added later when their quality, freshness, and commercial
  incentives can be governed explicitly.
