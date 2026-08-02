# 0025 — Authenticated saved-jobs API

Status: Accepted

Date: 2026-08-02

## Context

Solara Hire already has owner-scoped saved-job persistence and a verified browser identity, but
the web product has no supported HTTP contract for saved jobs. Application tracking has a larger
status workflow and should not be coupled to the first account feature.

## Decision

- Expose saved jobs as a dedicated authenticated `/api/v1/saved-jobs` resource.
- Require a verified principal for every read and mutation; anonymous compatibility does not
  apply to account data.
- Use `PUT /saved-jobs/{job_id}` because saving and updating notes are idempotent for the existing
  `(user_id, job_id)` key.
- Return the canonical job alongside saved-job metadata so clients do not need an N+1 detail
  request.
- Return the same not-found response when a saved job belongs to another account or does not
  exist.
- Keep application creation, status transitions, and tracking UI in later subphases.

## Consequences

- Saved-job ownership is enforced by the verified principal rather than any client-supplied user
  identifier.
- The frontend can add optimistic save controls against one stable server contract.
- Notes remain optional and bounded; raw resume content and provider credentials never enter the
  saved-job record.
- Assisted application tracking can evolve independently without destabilizing this resource.
