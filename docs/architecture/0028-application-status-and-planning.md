# ADR 0028: Manual application status and planning metadata

- Status: Accepted
- Date: 2026-08-02

## Context

Job discovery providers expose openings, not a user's private employer-side application state.
Solara Hire must represent stages such as under review or rejected without implying that an
aggregator or ATS reported an event it cannot access. Users also need to adjust a next action or
deadline without manufacturing a status transition.

## Decision

Keep application status user-confirmed. Add `Under review` as an explicit stage after `Applied`
and before assessment or interview outcomes. Continue to record each confirmed status transition
as an immutable event.

Expose a separate owner-scoped planning update that replaces the tracker's notes, next action,
and next-action deadline without adding a status event. Planning changes update the tracker's
`updated_at` value but do not claim that an employer changed the application.

Provider discovery remains isolated from private application state. Future email or ATS
integrations may propose a status change, but applying that proposal must remain an explicit,
auditable user action.

## Consequences

- The tracker can describe common real-world progress more accurately.
- Status history remains factual and distinct from personal planning edits.
- Deadlines become structured data that a later reminder worker can query.
- Automatic employer-status synchronization remains intentionally out of scope.
