# ADR 0021: Asynchronous job discovery boundary

- Status: Accepted
- Date: 2026-08-02

## Context

Synchronous provider discovery keeps an HTTP request open while several external systems respond.
That makes normal provider latency look like a frozen interface and couples request timeouts to the
slowest provider. Phase 5D needs the first user-facing background operation while retaining the
working synchronous endpoint as a rollback path.

Resume contents and recommendation scoring are intentionally out of scope. They require separate
privacy, factuality, cost, and idempotency decisions.

## Decision

Add a purpose-built `job.discovery` operation with this browser contract:

1. `POST /api/v1/jobs/search-tasks` accepts normalized search preferences and an
   `Idempotency-Key`, persists the intent, and publishes only the task UUID.
2. A Dramatiq actor loads the intent from PostgreSQL, calls the existing provider orchestration,
   persists normalized jobs plus their stable order, and completes the durable task lifecycle.
3. `GET /api/v1/jobs/search-tasks/{task_id}` returns queued, running, failed, or succeeded state.
4. The browser polls through the Next.js same-origin boundary and begins recommendation ranking
   only after discovery succeeds.

Search input, provider coverage, and ordered job references live in dedicated relational tables.
The generic `background_tasks` table remains free of arbitrary payloads, provider responses,
resume data, and credentials. Redis remains a delivery mechanism rather than a result store.

Anonymous task access requires a stateless HMAC capability in `X-Task-Token`. Task UUID knowledge
alone is insufficient. The token is kept in browser memory, never put into a URL, and compared in
constant time. A process-local random secret supports single-process development when
`TASK_TOKEN_SECRET` is absent; every multi-process or production API deployment must configure
one shared secret of at least 32 bytes.

Idempotent retries may republish a queued task UUID. The transactional runner makes duplicate
delivery harmless. This deliberately closes the failure window in which PostgreSQL commits but
broker publication fails without introducing an outbox table in this milestone.

The existing synchronous `/api/v1/jobs/search` endpoint remains available. The frontend uses it
only when background workers are not configured, giving local development and rollback a bounded
compatibility path.

## Consequences

- Provider latency no longer consumes one long browser-to-API request.
- Users receive accessible queued and running progress states.
- API replicas must share `TASK_TOKEN_SECRET`; otherwise capabilities become replica-local.
- A queued task can receive duplicate messages, but completed external work is not repeated.
- Phase 5E still needs stale-running reconciliation, task expiry/retention, cancellation, metrics,
  and a transactional outbox decision before horizontal production scale.
