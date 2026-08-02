# ADR 0026: Authenticated application-tracking API

- Status: Accepted
- Date: 2026-08-02

## Context

Solara Hire has an authenticated, owner-scoped persistence boundary and an append-only
application lifecycle model, but no public API exposes that model to the canonical Next.js
client. The API must support a useful tracker without creating an unattended application or
allowing clients to invent lifecycle jumps.

## Decision

Expose `/api/v1/applications` only to verified authenticated principals. A new tracker:

- belongs to the principal and one canonical catalog job;
- may reference only a resume owned by that principal;
- starts at `Preparing`;
- preserves one tracker per user and job;
- exposes the legal next statuses derived from the server transition graph.

List responses embed the canonical job but omit event history. Detail and transition responses
include the append-only event history. Status changes use a dedicated transition endpoint and
return a conflict when the requested move is not legal. Cross-owner resources use the same
not-found response as missing resources.

No delete endpoint is exposed. Rejected and withdrawn records remain durable audit history, and
this API never submits an application to an employer.

## Consequences

- The tracker UI can render server-authoritative actions instead of duplicating workflow rules.
- User notes and status changes remain explainable and auditable.
- A later UI milestone can add board and timeline views without changing persistence.
- Editing tracker metadata without a status change and importing already-submitted applications
  remain later, explicit product decisions.
