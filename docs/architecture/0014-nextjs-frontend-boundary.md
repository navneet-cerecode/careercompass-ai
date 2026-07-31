# ADR 0014: Next.js frontend and generated API boundary

- Status: Accepted
- Date: 2026-08-01

## Context

CareerCompass needs to migrate from Streamlit to a production browser experience without
duplicating Pydantic contracts in TypeScript, exposing backend credentials, or removing the
working prototype before feature parity.

## Decision

Add an isolated `frontend/` application using Next.js App Router, React, and strict TypeScript.
Keep Streamlit operational throughout Phase 4.

FastAPI's OpenAPI document is the source of truth for frontend HTTP types. A deterministic Python
exporter writes the OpenAPI document, and `openapi-typescript` generates declarations committed
beside the frontend API client. CI regenerates both artifacts and fails if the committed contract
is stale.

Use `CAREERCOMPASS_API_URL` only in the Next.js server runtime. Browser components will use
server-rendered data or narrowly scoped Next.js route handlers introduced with each feature. Do
not expose provider keys, database credentials, or the internal API base URL through
`NEXT_PUBLIC_*` variables.

Phase 4A exposes only the existing liveness contract. Saved jobs and application mutations remain
unexposed until authentication provides a verified user identity.

## Consequences

- Pydantic and OpenAPI remain the canonical API contract.
- Frontend compilation detects backend contract drift.
- The browser bundle contains no backend credentials.
- The initial page remains usable in an explicit preview state when FastAPI is offline.
- Streamlit provides a low-risk rollback until Phase 4 feature parity is approved.
- Browser-to-backend mutation patterns will be added incrementally rather than through a generic
  unauthenticated proxy.
