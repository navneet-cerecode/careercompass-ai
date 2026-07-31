# ADR 0008: Use Synchronous SQLAlchemy and Alembic for Persistence

- Status: Accepted
- Date: 2026-08-01

## Context

CareerCompass needs PostgreSQL persistence, transaction boundaries, and reversible schema
migrations. Its current providers, file parsers, recommendation engine, and Streamlit facade are
synchronous.

## Decision

- Use SQLAlchemy 2.x ORM and Core with synchronous sessions.
- Use Psycopg 3 for PostgreSQL connectivity.
- Use Alembic for versioned upgrade and downgrade migrations.
- Require an explicit secret `DATABASE_URL` when persistence is constructed.
- Keep engine creation and database connections out of application import and startup paths.
- Use one transaction-scoped session per repository operation or API request.
- Adopt deterministic constraint naming before creating product tables.

## Consequences

FastAPI will run blocking persistence work in its thread pool, matching the existing service
architecture. Tests can exercise transaction and migration behavior with isolated SQLite
databases, while the Phase 3 integration gate will add PostgreSQL-specific verification. Moving
to async database access later would require evidence that it improves actual workload behavior.
