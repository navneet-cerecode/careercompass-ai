# 0030 — Application reminder web experience

Status: accepted

## Context

The durable reminder records introduced in ADR 0029 need a visible, accessible
product surface. Authentication tokens must remain server-side, and reminders
must preserve the review-first distinction between a user's plan and an
employer-confirmed status.

## Decision

Render a small interactive reminder center inside the otherwise server-rendered
site header. The client component talks only to authenticated Next.js route
handlers; those handlers attach the server session's API token and proxy the
owner-scoped FastAPI reminder endpoints.

The panel:

- shows an unread count without exposing reminder content in the page title;
- distinguishes overdue, today, and upcoming deadlines;
- lets the user mark a reminder read or dismiss it;
- links directly to and focuses the matching application tracker card;
- refreshes on page focus, after planning edits, and at a bounded one-minute
  interval; and
- states that reminders come only from user-authored deadlines and do not infer
  employer status.

The component remains a narrow client boundary so static header, navigation,
account, and page content stay server-rendered.

## Consequences

- Reminder content remains private behind verified authentication.
- Read and dismissal changes are durable across devices.
- Deadline delivery can lag by the maintenance schedule plus the bounded client
  refresh interval.
- Email, push, calendar, and ATS delivery remain out of scope until explicit
  consent, provenance, retry, and unsubscribe policies are designed.
