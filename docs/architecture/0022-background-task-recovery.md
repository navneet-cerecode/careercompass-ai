# ADR 0022: Background-task recovery, cancellation, and publication

- Status: Accepted
- Date: 2026-08-02

## Context

The Phase 5D discovery task can survive an HTTP timeout, but three crash windows remain:

- PostgreSQL can commit a queued task immediately before Redis publication fails.
- A worker can die after marking a task `running`.
- A user can leave or cancel while a blocking provider request is already executing.

Redis acknowledgement alone cannot prove durable product state. Killing a provider call from
another thread is unsafe, and retaining anonymous task history forever is unnecessary.

## Decision

Use PostgreSQL as the recovery authority:

1. Creating a discovery task also creates one `task_outbox` record in the same transaction.
2. Publication marks the outbox record only after Redis accepts the message. Failed publication
   remains pending for the next maintenance cycle.
3. Published tasks that remain queued are eligible for bounded redelivery. Duplicate delivery is
   harmless because the lifecycle row is locked before execution.
4. Workers update `heartbeat_at` while an operation runs.
5. Maintenance returns stale running work to `queued` while attempts remain, otherwise it records
   `stale_worker_timeout`.
6. Queued work exceeding the total queue lifetime fails with `queue_expired`.
7. Terminal task history is deleted after the configured retention period; product-specific rows
   and outbox records cascade from the task.

Cancellation is cooperative. Queued work cancels immediately. Running work records
`cancel_requested_at`; the current provider call may finish, but cancellation wins before the
generic lifecycle can report success or schedule another retry. Resume data, provider payloads,
tokens, and exception text remain absent from both the task row and outbox.

A `task_maintenance` actor runs one bounded batch. Scheduling is an infrastructure responsibility:
a platform scheduler invokes `python -m workers.enqueue_maintenance` at least once per configured
delivery-retry interval. The command publishes no user data.

Readiness now verifies PostgreSQL and Redis connectivity and returns HTTP 503 when either required
dependency is unavailable. Liveness remains dependency-free.

## Consequences

- Database commit and message publication no longer form an unrecoverable gap.
- Worker crashes and lost Redis messages recover without unattended provider duplication after a
  task has reached a terminal state.
- Cancellation does not promise unsafe hard interruption.
- Operators must schedule maintenance; running only the Dramatiq worker is insufficient.
- Outbox publication remains at-least-once. Exactly-once external provider calls are neither
  claimed nor required.
- Future authenticated tasks can use the same lifecycle with owner-scoped cancellation.
