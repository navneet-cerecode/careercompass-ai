# ADR 0009: Persist Canonical Jobs Separately from Provider Sources

- Status: Accepted
- Date: 2026-08-01

## Context

The Phase 2 process-local catalog could not support restarts or multiple API workers. A single
posting may also be discovered through an aggregator and a company ATS, so treating every source
result as a separate job loses attribution and creates duplicates.

## Decision

- Persist one canonical `jobs` record for each stable company/title/location fingerprint.
- Persist every contributing provider listing in `job_sources`.
- Keep provider external IDs and original source URLs outside the canonical job identity.
- Upsert jobs transactionally and retain the richer description when duplicates merge.
- Return durable database UUIDs from job search responses.
- Require configured persistence for search, detail, and recommendation job lookup.
- Keep application import and health endpoints independent of database connectivity.

## Consequences

Job detail links now survive process restarts and work across API workers. The first fingerprint
algorithm intentionally matches the existing deterministic deduplication rule; future similarity
matching can version and backfill fingerprints through an explicit migration. Database-backed
routes return a stable service error when persistence is not configured.
