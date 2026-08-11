# ADR 0048: Read-only Lever postings

- Status: Accepted
- Date: 2026-08-11

## Context

Lever exposes published public postings through a site-scoped JSON endpoint. Responses include a
stable posting ID, structured locations, work arrangement, job content, and hosted review and
application URLs. The same API family can accept applications, which exceeds the current
review-first discovery scope.

## Decision

Add a reusable Lever adapter and initially enable only live-verified Dun & Bradstreet India and Fam
feeds. Fetch each configured public site once per search, enforce title and location relevance
locally, and paginate the filtered results in memory.

Use Lever's posting ID as stable identity and preserve the hosted job page as both source and user
review URL. Do not call the application endpoint or collect candidate data.

## Consequences

- Direct India coverage expands across finance, operations, customer service, sales, marketing,
  partnerships, apprenticeships, design, product, data, and engineering.
- The provider favors precision over recall because Lever does not offer full-text search.
- New company feeds require live verification and an explicit registry change.
- Application submission and ATS status synchronization remain separate, consent-driven phases.
