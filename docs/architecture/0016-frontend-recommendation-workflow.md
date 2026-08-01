# ADR 0016: Stateless frontend discovery and recommendation workflow

- Status: Accepted
- Date: 2026-08-01

## Context

Phase 4C needs to connect a user-reviewed resume to live job discovery and explainable ranking
without adding anonymous persistence, exposing the internal FastAPI origin, or allowing the
browser to call arbitrary backend paths.

## Decision

Keep the complete profile, preferences, search response, and recommendations in the current
client component workflow. Add two fixed-purpose Next.js route handlers:

- `/api/jobs/search` forwards a bounded JSON search request to `/api/v1/jobs/search`.
- `/api/recommendations` forwards the reviewed resume and returned job IDs to
  `/api/v1/recommendations`.

Both handlers accept JSON only, enforce request-size ceilings, use server-only API configuration,
disable response caching, preserve stable FastAPI errors, and convert transport failures into
non-sensitive service errors. Generated OpenAPI declarations remain the frontend source of truth.

The browser sends the exact parser response when requesting recommendations. It does not infer,
rewrite, or add resume evidence. Results expose overall score, score components, matching and
missing skills, algorithm version, provider coverage, and suggested preparation. The only
application action opens the verified job URL for user review.

## Consequences

- Anonymous searches and rankings remain detached from user history, matching the persistence
  policy in ADR 0011.
- Refreshing the workspace clears the workflow and its sensitive resume text.
- Job-provider credentials, database settings, and the FastAPI origin remain outside the browser.
- Partial provider success is usable and explicitly disclosed.
- Saving jobs, tracking applications, and restoring sessions still require authenticated
  identity in later phases.
