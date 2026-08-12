# Production deployment runbook

## Supported topology

The portable production topology contains four release responsibilities:

1. Run `alembic upgrade head` as a one-shot release task.
2. Run the FastAPI image behind a TLS-terminating reverse proxy or load balancer.
3. Run the Dramatiq worker from the same immutable API image.
4. Run the standalone Next.js image behind the public HTTPS origin.

PostgreSQL and Redis should be managed services with encrypted connections,
backups, access controls, and private networking. `compose.production.yaml` is a
single-host validation topology, not a substitute for managed infrastructure.

The first shared staging environment is defined by `render.yaml`. It uses Render's
Singapore region, paid starter compute, a persistent Key Value queue, and a small
paid PostgreSQL instance. Creating the Blueprint provisions billable resources, so
review the current Render estimate before applying it. Render prompts for every
`sync: false` identity and provider credential; do not replace those declarations
with committed values.

After the first Blueprint sync, add the assigned frontend HTTPS origin to Auth0's
Allowed Callback URLs as `<origin>/auth/callback`, Allowed Logout URLs as `<origin>`,
and Allowed Web Origins as `<origin>`. Then rerun the production environment gate
inside the API and frontend services and complete the release gate below.

## Secrets and configuration

Copy `.env.production.example` to `.env.production` outside version control and
replace every placeholder. Never commit that file. Use the deployment platform's
secret manager for database, Redis, Auth0, Groq, RapidAPI, task-token, analytics,
and session secrets.

Run this fail-closed diagnostic before building or deploying:

```powershell
venv\Scripts\python.exe -m scripts.check_production_env
```

The diagnostic prints only missing or invalid variable names, never values.
Production startup additionally requires explicit API hostnames and HTTPS Auth0
issuer/JWKS endpoints.

The gate also requires browser and API audiences to match, the Auth0 domain to
match the issuer and signing-key hosts, and the public application and canonical
URLs to share one HTTPS origin. `SOLARAHIRE_API_URL` is the server-only route from
Next.js to FastAPI; in Compose it is `http://api:8000` and is never exposed to
browser code.

Validate the release graph without starting containers:

```powershell
$env:SOLARAHIRE_ENV_FILE = ".env.production"
docker compose --env-file .env.production -f compose.production.yaml --profile operations config --quiet
docker build --check -f Dockerfile.api .
docker build --check -f frontend/Dockerfile frontend
```

## Build and release

```powershell
docker compose --env-file .env.production -f compose.production.yaml build
docker compose --env-file .env.production -f compose.production.yaml run --rm migrate
docker compose --env-file .env.production -f compose.production.yaml up -d api worker frontend
```

Do not run two migration jobs concurrently. The API image runs as a non-root user,
uses a read-only filesystem, and exposes only its internal port. The example binds
the frontend to loopback; place a TLS reverse proxy in front of it before external
traffic is allowed.

The reverse proxy or edge platform must terminate TLS, cap request bodies,
rate-limit authentication, upload, and search endpoints, and forward only known
hostnames. Keep the API private whenever the frontend proxy is its only caller.
The API image bakes the approved semantic model at a fixed repository revision and
runs Hugging Face/Transformers in offline mode. A release therefore fails during
the controlled image build if that model cannot be resolved, instead of failing on
a user's first recommendation request. Review model provenance and license before
changing the pinned revision.

The API container reports healthy only when PostgreSQL and Redis are ready. API,
worker, and frontend processes run behind an init process and receive bounded
graceful shutdown windows. Keep the worker grace period longer than
`WORKER_TIME_LIMIT_MS` so a normal rollout does not interrupt accepted work.

## Scheduled maintenance

Run the following command at least every two minutes through the platform's job
scheduler. Overlapping runs are safe, but should still be avoided operationally.

```powershell
python -m workers.enqueue_maintenance
```

The Compose topology exposes the same one-shot operation for rehearsal and
schedulers that can execute container jobs:

```powershell
docker compose --env-file .env.production -f compose.production.yaml --profile operations run --rm maintenance
```

This reconciles task delivery, expires stale work, purges retained task history,
and creates user-controlled in-app reminders. It does not change employer-derived
application statuses.

## Release gate

Before routing traffic:

1. Verify `/api/v1/health/live` returns HTTP 200.
2. Verify `/api/v1/health/ready` returns HTTP 200 with database and broker `ok`.
3. Confirm migrations are at `head`.
4. Run the authenticated resume, search, recommendation, saved-job, and tracker smoke flow.
5. Confirm `X-Request-ID` appears on browser proxy and API responses.
6. Confirm no request bodies, tokens, résumé content, emails, or notes appear in logs.
7. Confirm Auth0 callback/logout URLs use the exact public HTTPS origin.
8. Confirm backups, alert routing, retention, and rollback ownership.

Confirm the migration graph without changing it:

```powershell
docker compose --env-file .env.production -f compose.production.yaml run --rm migrate alembic current --check-heads
```

## Backup and restore rehearsal

Before a schema-changing release, create a managed PostgreSQL snapshot and record
its identifier in the release ticket. At least quarterly, restore a recent backup
into an isolated, access-restricted database and verify:

1. `alembic current --check-heads` succeeds against the restored database.
2. Row counts for users, resumes, jobs, applications, and background tasks are plausible.
3. A read-only API smoke test succeeds with outbound provider calls disabled.
4. The measured recovery time and recovery point meet the agreed RTO and RPO.
5. The isolated restore and temporary credentials are destroyed after evidence is retained.

Redis is not the durable source of truth and is not restored as application data.
Queued work is reconciled from PostgreSQL through the maintenance operation.

## Rollback

Record immutable API and frontend image digests before release. Roll back API,
worker, and frontend images together, then rerun liveness, readiness, Auth0, and
authenticated workflow smoke checks. Do not downgrade the database unless that
specific migration has a reviewed rollback procedure. Prefer backward-compatible
expand/contract migrations; database restore is an incident operation requiring
explicit approval because it can discard writes made after the recovery point.
