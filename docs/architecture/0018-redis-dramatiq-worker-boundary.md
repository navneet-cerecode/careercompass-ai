# ADR 0018: Redis and Dramatiq background-worker boundary

- Status: Accepted
- Date: 2026-08-02

## Context

Provider discovery and future AI document generation can exceed a safe interactive HTTP request
window. CareerCompass needs retryable background execution without moving durable product state
out of PostgreSQL or causing API imports to connect to infrastructure.

The application services and persistence layer are synchronous. The worker foundation must
support Python 3.13, Redis, bounded retries, execution limits, dead letters, and offline unit
tests. Resume contents and credentials must not be copied into logs or broker messages.

## Decision

Use Dramatiq 2.2 with Redis as the message broker.

- PostgreSQL remains the durable source of truth for task state and product results.
- Redis coordinates message delivery and is not a result database.
- Broker construction is lazy and belongs to an explicit worker runtime.
- FastAPI, Streamlit, migrations, and offline tests must import without Redis.
- Broker URLs are secret settings and must not appear in representations or logs.
- Messages will contain identifiers and bounded JSON metadata, not raw resume files, resume text,
  API keys, or database credentials.
- Every production actor must define bounded retries, a message age, an execution limit, and an
  idempotent application-service operation.
- The local Redis port binds to loopback only. Production uses a managed private endpoint with
  authentication and transport encryption.

Phase 5A establishes infrastructure and configuration only. Durable task records, actors, API
task endpoints, and frontend progress behavior belong to later Phase 5 subphases.

## Alternatives considered

### Celery

Celery is mature and feature-rich, but its broader result-backend and workflow surface is not
needed for the initial CareerCompass boundary. Dramatiq provides the required Redis broker,
retry, dead-letter, time-limit, and test-broker capabilities with less application integration.

### In-process FastAPI background tasks

In-process tasks do not survive process restarts, do not provide a shared queue across API
workers, and cannot form the production execution boundary required for long-running work.

### Redis as durable task storage

Rejected. Queue retention and product-history retention have different guarantees. PostgreSQL
will own durable task state beginning in Phase 5B.

## Consequences

- Redis becomes required only for worker-backed operations.
- Worker dependencies are isolated in `requirements-worker.txt`.
- Local development gains a repository-managed Redis service and persistent local broker volume.
- Later task implementations must be idempotent because delivery is at least once.
- Phase 5B must add durable task ownership and lifecycle records before sensitive user work is
  accepted.
