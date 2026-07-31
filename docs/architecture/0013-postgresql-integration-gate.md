# ADR 0013: PostgreSQL integration gate

- Status: Accepted
- Date: 2026-08-01

## Context

SQLite tests are fast and useful for repository behavior, but they cannot verify PostgreSQL
types, transactional DDL, driver behavior, or the complete Alembic migration chain. Developer
workstations may not have a safe local PostgreSQL instance.

## Decision

CI starts a disposable PostgreSQL 16 service. A separately marked integration test:

1. requires an explicit `TEST_DATABASE_URL` using the PostgreSQL dialect;
2. downgrades the dedicated database to `base`;
3. upgrades the complete Alembic chain to `head`;
4. verifies the recorded revision and database health;
5. executes owner-scoped job, saved-job, and application repositories;
6. downgrades the database to `base` in a `finally` block.

The gate is destructive by design and must only target a disposable test database. Local offline
tests skip it when `TEST_DATABASE_URL` is absent. CI runs offline and PostgreSQL tests as distinct
steps so the failure boundary remains clear.

## Consequences

- PostgreSQL compatibility is enforced on every push and pull request.
- Developers without PostgreSQL can still run the complete offline suite.
- Migration failures are separated from unit-test failures.
- PostgreSQL credentials used by CI are ephemeral test-only values.
- Production migrations remain an explicit deployment operation; application startup does not
  mutate the schema.
