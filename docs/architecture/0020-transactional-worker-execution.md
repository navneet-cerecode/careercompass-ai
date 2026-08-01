# ADR 0020: Transactional worker execution boundary

- Status: Accepted
- Date: 2026-08-02

## Context

ADR 0018 established Redis and Dramatiq delivery, and ADR 0019 established durable PostgreSQL task
state. Phase 5C needs an executable worker that connects those boundaries without holding a
database transaction open during provider or AI work, logging sensitive exceptions, or executing
the same completed task twice after duplicate delivery.

No production background product operation is ready yet. The first actor must therefore prove
the runtime without calling a paid service or processing resume data.

## Decision

Add an internal `system.probe` actor and a reusable `BackgroundTaskRunner`.

The runner:

1. locks and transitions the task from `queued` to `running` in a short transaction;
2. commits that transition before calling the operation;
3. runs the operation without an open database transaction;
4. records success, a bounded retry, or terminal failure in a new transaction;
5. converts unexpected operation exceptions to the safe code `unexpected_error`;
6. suppresses duplicate delivery for terminal or already-running tasks.

The actor accepts task and optional user UUID strings only. It carries no resume text, files,
provider payloads, credentials, or arbitrary user input. Invalid identifiers and unavailable
tasks are rejected without exposing database details.

Every actor defines a queue, maximum retries, retry backoff, execution limit, and message age.
Retryable application failures raise a sanitized worker exception only while the durable record
has attempts remaining. The task record, rather than the Redis result backend, is authoritative.

The production entrypoint constructs Redis and database dependencies explicitly. API and
Streamlit imports remain independent of the worker runtime. Database pools are disposed during
worker shutdown.

## Transaction limitation

An operation and its final database update cannot be one atomic transaction without holding a
connection throughout long-running external work. Product operations added later must therefore
be idempotent. Phase 5E must add stale-running-task detection and reconciliation for the rare case
where an operation finishes but its final lifecycle transaction cannot be committed.

## Consequences

- Real messages can execute through Redis and update durable PostgreSQL state.
- The initial actor is safe to run locally and in CI without provider cost or personal data.
- Duplicate completed messages do not repeat the operation.
- Unexpected exception messages are not copied into task records or worker logs.
- Phase 5D can add task APIs and frontend progress behavior without embedding execution logic in
  HTTP handlers.
