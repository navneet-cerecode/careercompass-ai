# Background-task operations

## Required processes

Production needs all four components:

1. PostgreSQL with migrations at `head`.
2. Redis.
3. The Dramatiq worker:

   ```powershell
   python -m dramatiq workers.entrypoint --processes 1 --threads 4
   ```

4. A scheduler that runs this command at least every two minutes:

   ```powershell
   python -m workers.enqueue_maintenance
   ```

Every API replica must use the same `TASK_TOKEN_SECRET`. Use a random secret of at least 32 bytes
from the deployment secret manager; never commit it.

## Readiness

`GET /api/v1/health/live` confirms only that the API process is responsive.

`GET /api/v1/health/ready` checks PostgreSQL and Redis. It returns HTTP 503 with bounded check names
when a dependency is missing or unavailable. It never returns connection strings or exception
details.

## Recovery settings

- `WORKER_HEARTBEAT_SECONDS`: running-task heartbeat interval.
- `TASK_STALE_AFTER_SECONDS`: age after which a missing heartbeat is recoverable.
- `TASK_DELIVERY_RETRY_SECONDS`: queued-message redelivery interval.
- `TASK_QUEUE_EXPIRY_SECONDS`: maximum total queued lifetime.
- `TASK_RETENTION_DAYS`: terminal-history retention.
- `TASK_MAINTENANCE_BATCH_SIZE`: maximum records handled per cycle.

Keep `TASK_STALE_AFTER_SECONDS` comfortably above the heartbeat interval. The defaults use a
30-second heartbeat and a 10-minute stale threshold.

## Safe failure signals

Task records expose machine codes only:

- `delivery_recovered`
- `stale_worker_recovered`
- `stale_worker_timeout`
- `queue_expired`
- `cancelled_by_user`

Provider response bodies, resume content, credentials, and raw exception messages must not be
added to task records or maintenance logs.
