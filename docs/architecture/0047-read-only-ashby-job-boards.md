# ADR 0047: Read-only Ashby job boards

- Status: Accepted
- Date: 2026-08-11

## Context

Ashby exposes currently published postings through a lightweight public endpoint for each hosted
job board. The response includes structured location, employment type, plain-text description,
listing visibility, and hosted job URLs. Ashby also offers authenticated application endpoints,
which exceed the current review-first discovery scope.

## Decision

Add a reusable Ashby adapter and initially enable only live-verified Aspora and Riveron feeds.
Fetch each configured board once per search, require `isListed` to be true, enforce title and
location relevance locally, and paginate the filtered result in memory.

Use Ashby's posting ID as stable identity and preserve the hosted job page as both source and user
review URL. Do not call the application form or candidate submission APIs.

## Consequences

- Direct India coverage expands across finance, transaction services, operations, product, design,
  customer support, consulting, and engineering.
- Unlisted direct-link postings are not exposed through Solara Hire.
- New company feeds require live verification and an explicit registry change.
- Application submission and ATS status synchronization remain separate, consent-driven phases.
