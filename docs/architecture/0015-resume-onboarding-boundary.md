# ADR 0015: Resume onboarding through a narrow frontend boundary

- Status: Accepted
- Date: 2026-08-01

## Context

The Next.js workspace needs to parse user resumes through FastAPI without exposing the internal
API origin to the browser, duplicating resume schemas, persisting sensitive source text, or
creating a generic unauthenticated backend proxy.

## Decision

Add one purpose-built Next.js route handler at `/api/resumes/parse`. It accepts one PDF, DOCX, or
plain-text resume, applies the frontend's 5 MB upload boundary, and forwards only that file to
FastAPI's existing `/api/v1/resumes/parse` endpoint. The internal API URL remains server-only.

The interactive workspace uses the generated OpenAPI types for its success contract and preserves
FastAPI's stable error messages. Parsed fields and original source text live only in client
component state for user review; Phase 4B introduces no browser storage or persistence.

The review surface displays only fields returned by the parser and explicitly states that nothing
was added or embellished. It does not offer job ranking, saving, or application actions until
their own approved phases establish the required state and identity boundaries.

## Consequences

- Resume contents cross a narrow, auditable browser-to-Next-to-FastAPI path.
- Provider keys and the FastAPI origin remain outside the browser bundle.
- Client and proxy size checks improve feedback and limit conventional oversized requests;
  FastAPI remains the canonical upload validator.
- Refreshing or leaving the workspace clears the parsed client state.
- Authentication and encrypted resume persistence remain separate future decisions.
