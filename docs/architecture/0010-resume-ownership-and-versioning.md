# ADR 0010: Persist Resumes as Owner-Scoped Immutable Versions

- Status: Accepted
- Date: 2026-08-01

## Context

CareerCompass needs durable resumes and reusable normalized skills, but authentication is not yet
implemented. Resume content is sensitive, and silently overwriting a parsed profile would make
recommendations difficult to reproduce.

## Decision

- Create ownership-ready users without password, token, or OAuth fields.
- Store every resume revision as a new owner-scoped version.
- Mark one version active without deleting prior versions.
- Normalize skills into a shared table and link them to resume versions.
- Scope all resume reads by both user ID and resume ID.
- Store a content hash for integrity and future duplicate detection.
- Do not expose user or resume persistence through unauthenticated public routes.
- Never write raw resume content to application logs.

## Consequences

Repositories can support future authenticated APIs without redesigning ownership. Resume history
and the exact source text used for a recommendation remain reproducible. Database encryption,
backup controls, retention, deletion, and object-storage policy still require production
infrastructure work before sensitive user data is accepted in a deployed environment.
