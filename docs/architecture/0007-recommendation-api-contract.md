# ADR 0007: Keep Recommendation Requests Stateless for Resume Data

- Status: Accepted
- Date: 2026-08-01

## Context

Phase 2 has no authenticated resume repository. Persisting sensitive resume content in a
process-local cache would create ambiguous privacy and lifecycle behavior. Recommendation jobs,
however, must correspond to normalized results returned by discovery.

## Decision

- Recommendation requests send user-reviewed resume content explicitly.
- Requests reference jobs by IDs previously returned from the process-local job catalog.
- The API maps transport input into the canonical `Resume` model.
- Both FastAPI and Streamlit call the same `RecommendationService`.
- Embedding and ranking services remain lazy and are created only on the first recommendation.
- Ranking failures return a stable error without exposing resume content or implementation details.

## Consequences

The API does not retain resume content after a request. Clients must resend reviewed resume data
until Phase 3 introduces authenticated persistence. Job IDs remain subject to the transitional
catalog limitations documented in ADR 0006.
