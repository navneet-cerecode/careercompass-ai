# ADR 0017: Next.js canonical frontend with Streamlit fallback

- Status: Accepted
- Date: 2026-08-01

## Context

The Phase 4 Next.js workspace now covers resume onboarding, factual profile correction, explicit
search preferences, live multi-provider discovery, explainable ranking, and assisted outbound
application review. Repository documentation still identifies Streamlit as canonical, leaving
developers with conflicting startup paths and no objective cutover smoke gate.

The Streamlit AI Inspector can request an on-demand Groq narrative that is not exposed in the
web workflow. That synchronous legacy call should not force the standard product journey to
remain on Streamlit or be copied into the request path before the worker architecture exists.

## Decision

Adopt the Next.js application as the canonical user interface for the standard anonymous
CareerCompass workflow. Keep FastAPI as the HTTP boundary and Python services as the application
core.

Retain root `app.py` as a compatibility fallback. Freeze it for critical compatibility fixes;
new interface work belongs in Next.js. Record the Streamlit-only Groq narrative as an explicit,
non-blocking parity exception and revisit it through the Phase 5 background-work boundary.

Add a non-destructive smoke command that verifies API health and both canonical web routes
without calling paid providers, uploading personal data, or mutating persistence.

## Consequences

- New developers have one normal product startup path.
- Streamlit remains available for rollback and the legacy narrative exception.
- The repository can measure cutover readiness without live-provider cost or resume data.
- Streamlit removal remains a separate destructive change requiring explicit approval.
- Authentication, workers, subscriptions, and production deployment remain outside Phase 4.
