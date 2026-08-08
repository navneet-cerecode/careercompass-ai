# ADR 0039: Evidence-grounded interview readiness

- Status: Accepted
- Date: 2026-08-09

## Context

An application tracker can record an interview stage, but candidates benefit from preparing before
that stage and must not be encouraged to invent experience. Generic generated answers create a
factual-accuracy risk and do not serve the wide range of technical and non-technical roles Solara
Hire discovers.

## Decision

Attach at most one owner-scoped interview kit to a submitted application. Preparation is available
while the application is `Applied`, `Under review`, `Assessment`, or `Interview`; opening a kit
never changes the recorded employer status or implies that an interview was scheduled.

Question themes are created deterministically from the canonical job and the resume selected for
the application, falling back to the user's active resume. The kit covers career story, evidenced
role skills, an honest skill-gap prompt when appropriate, personal motivation, and behavior. It
shows short resume evidence prompts but never drafts a candidate answer or infers motivation.

The candidate owns all response text. Draft edits clear the prior review timestamp. A separate,
explicit action records that the candidate fact-checked the current notes. Kits and updates are
always scoped to the authenticated owner.

## Consequences

- Interview preparation works for technical and non-technical roles without an industry-specific
  question bank.
- Resume evidence is traceable and gaps are discussed honestly instead of being hidden.
- The application history remains a record of user-confirmed employer events, not product guesses.
- Future coaching or practice-session features can build on this record but must preserve the same
  evidence and explicit-review boundary.
