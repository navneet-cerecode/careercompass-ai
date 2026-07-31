# ADR 0006: Use a Bounded Transitional Job Catalog

- Status: Superseded by ADR 0009
- Date: 2026-08-01

## Context

Phase 2 requires a job-detail API before PostgreSQL is introduced in Phase 3. Canonical jobs have
runtime UUIDs, and no durable repository currently exists. Provider failures must also permit
partial search results.

## Decision

- Job discovery returns jobs plus bounded provider-failure metadata.
- One provider failure does not discard successful results from other providers.
- API search responses explicitly report complete, partial, or failed status.
- Jobs returned by searches are placed in a size-bounded, process-local catalog for detail lookup.
- Provider exception messages and credentials are never returned to API clients.

## Consequences

Detail lookup works only in the API process that performed the search and is not durable across
restarts or multiple workers. This limitation is explicit and will be removed when Phase 3 adds a
PostgreSQL job repository. The bounded catalog prevents unbounded process memory growth during the
transition.
