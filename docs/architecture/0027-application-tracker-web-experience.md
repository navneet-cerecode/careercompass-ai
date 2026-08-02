# ADR 0027: Application tracker web experience

- Status: Accepted
- Date: 2026-08-02

## Context

The authenticated application API now owns lifecycle rules and append-only history. The
canonical Next.js client needs to expose that capability without duplicating transition logic,
encouraging unattended applying, or moving bearer tokens into browser JavaScript.

## Decision

Add an authenticated `/applications` account page and same-origin Next.js route handlers for
the application API. Bearer tokens remain server-side. The client:

- groups trackers into preparation, active-process, and outcome views;
- renders only the `allowed_next_statuses` returned by FastAPI;
- requires an explicit form submission for every transition;
- loads immutable event history on demand;
- starts a tracker only after a user selects `Start tracking` from a saved role.

The interface can collect an optional transition note and next action. It never reports an
employer-side action automatically and never submits an application.

## Consequences

- The browser experience remains aligned with the server transition graph.
- Saved roles and application trackers have a deliberate, review-first handoff.
- Account tokens stay out of the client bundle and browser-visible requests.
- Deadlines can be displayed when present, while dedicated metadata editing and reminders remain
  later milestones.
