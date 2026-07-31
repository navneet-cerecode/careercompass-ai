# ADR 0002: Use one typed job-provider contract

- Status: Accepted
- Date: 2026-08-01

## Context

The prototype contained two different `BaseProvider` classes under `services/job_discovery` and
`services/jobs`. Active providers implemented only `search(role, location)`, provider-specific
normalization was embedded inside request loops, and the generic `APIProvider` name hid that the
implementation was specific to JSearch.

This duplication made provider capabilities unclear and would make additional aggregators and
ATS adapters difficult to test consistently.

## Decision

`services/job_discovery/providers` is the canonical provider package. Every provider implements:

- `provider_name`
- `capabilities`
- `search_jobs(JobSearchQuery)`
- `normalize_job(raw_job)`
- `get_job_details(external_id)` when supported
- `health_check()`

`JobSearchQuery`, `ProviderCapabilities`, `ProviderHealth`, and `ProviderConfig` are shared typed
contracts. Capability flags describe implemented adapter behavior, not theoretical upstream API
features.

JSearch is represented by the named `JSearchProvider`. Workday remains a reusable ATS adapter
configured for a company registry entry. Discovery accepts injected provider instances so
orchestration and failure behavior can be tested without credentials or network calls.

## Compatibility

- `APIProvider` remains an alias for `JSearchProvider`.
- The registry accepts the former `api` platform key as an alias for `jsearch`.
- `BaseProvider.search(role, location)` adapts to `search_jobs(JobSearchQuery)`.
- `services.jobs.providers.base_provider` re-exports the canonical contract.

No legacy import is deleted in this migration.

## Consequences

- Provider-specific payloads are normalized at a clear boundary.
- JSearch and Workday jobs carry accurate source attribution.
- Query validation and capability discovery are consistent.
- Recorded payload fixtures can test adapters without consuming API quotas.
- Concurrent fetching, retries, provider-level rate limits, live health checks, and partial
  success remain later reliability work; this decision does not pretend those features exist.
