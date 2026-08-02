# 0029 — Durable application reminders

Status: accepted

## Context

Application plans can include a user-authored next action and deadline. Solara Hire
needs to surface those deadlines reliably without claiming knowledge of an employer's
private hiring status or depending on a browser session remaining open.

## Decision

Store owner-scoped reminder records in PostgreSQL and reconcile them from application
plans during the existing scheduled maintenance cycle. A unique application/deadline
key makes repeated maintenance runs idempotent.

The first release is in-app only. Reminder state is user controlled (`unread`, `read`,
or `dismissed`). Changing or clearing a deadline, removing its next action, or moving
an application to `Rejected` or `Withdrawn` dismisses the superseded reminder.

Application status history remains separate. Creating or updating a reminder never
creates an application status event and never infers an employer decision.

## Consequences

- Deployments continue to operate one scheduled maintenance entry point.
- The API can serve reminders after restarts and across devices.
- Email, push, calendar, and ATS integrations remain future opt-in delivery channels
  with their own consent, retry, and provenance requirements.
