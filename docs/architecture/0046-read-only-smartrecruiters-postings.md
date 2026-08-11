# ADR 0046: Read-only SmartRecruiters postings

- Status: Accepted
- Date: 2026-08-11

## Context

SmartRecruiters exposes active public postings per company with role, country, and pagination
filters. Posting details include descriptions and application links. Separate authenticated APIs
can submit applications and retrieve candidate status, but those capabilities exceed the current
review-first discovery scope.

## Decision

Add a reusable SmartRecruiters adapter and initially enable only live-verified Bosch Group and
KredX India feeds. Query public postings by role and country, enforce title and location relevance
locally, and retrieve details only for accepted summaries. Construct detail requests from the known
SmartRecruiters API origin rather than following response-provided URLs.

Use posting UUID as stable identity when available and preserve the public SmartRecruiters listing
or apply URL. Do not integrate candidate creation or application-status endpoints.

## Consequences

- Direct India coverage expands across finance, sales, operations, manufacturing, and engineering.
- Detail calls are bounded by the requested page size and local relevance filter.
- New company feeds require a live verification and explicit registry change.
- Application submission and ATS status synchronization remain separate, consent-driven phases.
