# ADR 0045: Read-only curated Greenhouse boards

- Status: Accepted
- Date: 2026-08-11

## Context

Greenhouse exposes published jobs through public, unauthenticated GET endpoints, but each endpoint
represents one employer and provides no general role or location search. Registering arbitrary or
stale board tokens would create unreliable coverage and unnecessary network traffic.

## Decision

Add a reusable Greenhouse adapter and initially enable only live-verified Appian and Blenheim
Chalcot India boards. Fetch published jobs with descriptions, then enforce role and location
relevance locally before normalization. Remote listings are accepted only for an explicit remote
search. Use the Greenhouse post ID as provider identity and preserve the employer-hosted listing URL.

The integration is discovery-only. Solara Hire does not call Greenhouse's application submission
endpoint and continues to require user review before any external application action.

## Consequences

- India coverage expands across technical and non-technical roles without another secret.
- New boards require a live relevance check and an explicit registry change.
- The provider favors precision over recall because upstream filtering is unavailable.
- Provider failures remain isolated by the existing partial-coverage workflow.
