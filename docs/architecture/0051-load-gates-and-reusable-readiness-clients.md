# ADR 0051: Load gates and reusable readiness clients

- Status: Accepted
- Date: 2026-08-12

## Context

Provider concurrency reduced individual search latency, but the stack had no repeatable way to
measure API, frontend, dependency, or worker behavior under concurrent demand. Initial measurement
also showed that every readiness probe created and disposed a PostgreSQL engine and Redis broker.

## Decision

Keep performance validation dependency-free and explicit. A read-only HTTP gate measures liveness,
readiness, and Next.js routes. An isolated worker gate uses synthetic `system.probe` tasks, requires
a PostgreSQL database ending in `_test`, assigns a unique Redis namespace, and cleans up its records
and keys. The worker gate migrates only that validated test database before execution.

Reuse the API-owned PostgreSQL pool and Redis broker for readiness checks. The existing application
lifespan remains responsible for closing both resources. Continue checking each dependency on every
readiness request rather than caching health outcomes.

## Consequences

- Local and deployed regression profiles use the same small commands without a new load framework.
- Normal load validation sends no resume data and consumes no external job-provider quota.
- Repeated readiness probes avoid connection-client churn while still performing real database and
  broker checks.
- Synthetic worker benchmarks are forbidden from development and production databases by name.
- Local results establish regression baselines, not production capacity promises.
