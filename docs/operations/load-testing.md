# Load testing

The repository includes a dependency-free, read-only HTTP load gate. Its default targets separate
raw FastAPI capacity, PostgreSQL/Redis readiness pressure, and the canonical Next.js boundary:

```powershell
python scripts/load_test.py --requests 200 --concurrency 20
```

Use explicit targets for a deployed environment. Only target endpoints that are safe to repeat:

```powershell
python scripts/load_test.py `
  --target api-ready=https://api.example.com/api/v1/health/ready `
  --requests 500 --concurrency 25 --max-error-rate 0.01 --max-p95-ms 1000
```

`--json` prints machine-readable results. The command exits nonzero when the error-rate or optional
p95 threshold is exceeded. Run it from a separate host before a production launch; localhost
numbers are useful for regression comparisons, not capacity promises.

The default gate never sends resume data, credentials, writes, or job-provider requests. Exercise
authenticated and provider-backed workflows separately with synthetic accounts and explicit API
quotas; do not point an uncontrolled stress run at external aggregators.

## Worker throughput

The worker gate uses only synthetic `system.probe` tasks in a dedicated PostgreSQL database and a
unique Redis namespace. It refuses any database whose name does not end in `_test`, then removes
every task and namespaced Redis key it creates. The command migrates that dedicated database to the
current schema before the run:

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://user:password@localhost/solarahire_test"
$env:TEST_REDIS_URL = "redis://127.0.0.1:6379/15"
python -m scripts.stress_worker --tasks 100 --threads 4
```

Never place real credentials in shell history on shared machines; inject these variables from the
deployment secret manager. The probe operation contains no resume, job, or user data and makes no
external provider calls.

## Local baseline

On 2026-08-12, the production-mode local stack completed every request and task in these profiles:

| Boundary | Load | Throughput | p95 |
| --- | ---: | ---: | ---: |
| API liveness | 200 requests, concurrency 20 | 280.9 req/s | 84.9 ms |
| API readiness | 500 requests, concurrency 25 | 243.9 req/s | 116.2 ms |
| Next.js home | 200 requests, concurrency 20 | 77.6 req/s | 356.3 ms |
| Next.js workspace | 200 requests, concurrency 20 | 81.3 req/s | 337.3 ms |
| Worker probe | 100 tasks, 4 threads | 96.3 tasks/s | n/a |

The 2026-08-12 container rehearsal repeated the read-only boundary gate against the isolated
production Compose stack: 200/200 requests succeeded for each target, with p95 values of 31.6 ms
for API liveness, 116.6 ms for readiness, 173.0 ms for the home page, and 149.9 ms for the
workspace. The worker completed 100/100 synthetic tasks at 167.1 tasks/s. The same rehearsal
verified a PostgreSQL backup restored at migration revision 0017, scheduled maintenance was
consumed, and the worker handled SIGTERM gracefully.

These laptop-local values are regression references, not production capacity guarantees. The
readiness implementation reuses application-owned PostgreSQL and Redis clients; before that change,
the same 500-request profile achieved 65.5 req/s with a 929.0 ms p95.
