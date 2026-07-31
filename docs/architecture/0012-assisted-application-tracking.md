# ADR 0012: Assisted application tracking

- Status: Accepted
- Date: 2026-08-01

## Context

CareerCompass needs saved jobs and an application tracker, but authentication and an
authorized API principal do not exist yet. The product also explicitly favors user-reviewed
applications over unattended mass applying.

## Decision

Persist saved jobs by `(user_id, job_id)`. Persist one application tracker per user and job,
with an explicit status transition graph. Every creation and valid status change appends an
immutable application event containing the previous status, new status, timestamp, and an
optional user note.

Repository reads and mutations always include `user_id`. A selected resume must belong to the
same user. Invalid transitions fail without changing the tracker or adding an event. Rejected
and withdrawn trackers are terminal; offers may only be withdrawn.

Do not expose mutation endpoints until authentication can provide a verified user identity.
This phase creates no unattended application or provider-side submission capability.

## Consequences

- Saved jobs are idempotent and independently owned.
- Application history is explainable and auditable.
- UI and API clients cannot skip workflow stages accidentally.
- Future authentication can wrap the existing owner-scoped repositories.
- Reopening terminal applications, multiple attempts for the same job, and automated
  application submission require separate product decisions and migrations.
