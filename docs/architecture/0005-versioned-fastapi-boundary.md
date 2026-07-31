# ADR 0005: Introduce a Versioned FastAPI Boundary

- Status: Accepted
- Date: 2026-08-01

## Context

CareerCompass currently exposes product behavior only through Streamlit. The target architecture
requires a typed HTTP boundary that a future Next.js client can consume, while Streamlit must
continue to work during migration.

## Decision

- Add a FastAPI application factory under `api/`.
- Expose product routes below `/api/v1`.
- Keep transport models inside `api/schemas` rather than returning internal workflow state.
- Construct no provider, embedding, or LLM clients during API startup.
- Begin with liveness and readiness contracts before exposing product operations.
- Retain the existing root `app.py` as the Streamlit entry point.

## Consequences

The API can be tested with injected settings and started without external credentials. Future
endpoint versions can coexist without renaming domain models. Readiness currently confirms only
that application configuration loaded; database, queue, and object-storage checks will be added
when those dependencies exist.
