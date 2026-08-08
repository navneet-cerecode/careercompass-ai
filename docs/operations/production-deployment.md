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
The semantic matcher downloads its model into the container's temporary cache on
first use, so either permit that outbound request or bake an approved model into a
derived image. Temporary model caches are discarded whenever a container is
replaced.

## Scheduled maintenance

Run the following command at least every two minutes through the platform's job
scheduler. Overlapping runs are safe, but should still be avoided operationally.

```powershell
python -m workers.enqueue_maintenance
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

Rollback the application images together. Do not downgrade the database unless a
reviewed migration-specific rollback procedure exists.
