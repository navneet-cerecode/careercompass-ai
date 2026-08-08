# ADR 0038: Review-first application packets

- Status: Accepted
- Date: 2026-08-09

## Context

Solara Hire can track applications and produce user-verified resumes and cover letters. A direct
status transition from preparation to application, however, does not prove that the user reviewed
the target role, selected documents, or employer questions. It also makes an `Applied` status
ambiguous: the product must not imply that it submitted an external form.

## Decision

Attach one owner-scoped application packet to each tracked application. The packet records the
source resume, optional verified tailored resume, optional verified cover letter, and four explicit
review confirmations: job details, resume, selected cover letter, and employer questions.

Only documents verified by the same owner, created for the same canonical job, and grounded in the
same source resume may be selected. A packet becomes ready only after every applicable check is
complete. Readiness locks the packet and moves the tracker from `Preparing` to `Ready to apply`.

The user then continues on the external employer page. Solara Hire records `Applied` only after the
user checks an explicit submission confirmation. Generic status endpoints cannot bypass either
boundary. The application event history identifies the readiness decision and the user-confirmed
external submission; it never claims to have observed an ATS decision.

## Consequences

- Every ready application has a durable, reviewable preparation record.
- Tailored documents remain factually bounded by their verified source resume.
- External application forms, questions, consent, and final submission remain under user control.
- The tracker can honestly distinguish product-assisted preparation from employer-side events.
- Editing a locked packet requires a future explicit revision workflow rather than silent mutation.
