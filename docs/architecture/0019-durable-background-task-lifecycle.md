# ADR 0019: Durable idempotent background-task lifecycle

- Status: Accepted
- Date: 2026-08-02

## Context

The Redis and Dramatiq boundary in ADR 0018 coordinates message delivery, but a broker is not a
durable product-history database. CareerCompass needs a lifecycle record that survives broker
retention, process restarts, retries, and future horizontal scaling.

Authentication is not implemented yet. The schema must support authenticated ownership later
without assigning anonymous activity to a fabricated user. Task persistence must also avoid
turning resume contents, provider payloads, credentials, or exception messages into durable data.

## Decision

Persist background tasks in PostgreSQL with these states:

```text
queued -> running -> succeeded
   |         |
   |         +-> queued (bounded retry)
   |         +-> failed
   |
   +-> cancelled
```

- `user_id` is nullable until authentication supplies a verified owner.
- Owned and anonymous task reads are separate repository scopes.
- A task stores its type, optional resource identifier, attempt counts, safe error code, and
  lifecycle timestamps.
- Raw task inputs, resume text, files, provider responses, credentials, and exception messages
  are not stored in the task row.
- Idempotency keys are normalized only for surrounding whitespace and stored as SHA-256
  fingerprints scoped by owner and task type. Plaintext keys are not persisted.
- Reusing a key for the same task inputs returns the existing task. Reusing it for different
  inputs fails with an explicit conflict.
- State-changing repository reads acquire a row lock on databases that support `FOR UPDATE`.
- Attempts increment when work starts. Retryable failures return to `queued` only while attempts
  remain; otherwise the task becomes terminally `failed`.
- Only queued work can be cancelled in this phase. Running-task cancellation requires a separate
  cooperative-cancellation design.

Phase 5B creates no API endpoints and enqueues no work. Anonymous task retrieval must not be
exposed until a later phase defines an opaque access capability.

## Consequences

- Task history remains available even when Redis messages expire.
- At-least-once message delivery can be paired with idempotent application operations.
- Sensitive task inputs must live behind purpose-built product records or short-lived secure
  transport boundaries rather than the generic task table.
- Authentication can make `user_id` mandatory at the API boundary without redesigning storage.
- Phase 5C can add actors that update this lifecycle before and after application-service calls.
