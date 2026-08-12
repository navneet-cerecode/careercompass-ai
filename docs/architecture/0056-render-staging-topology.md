# 0056. Use a Render Blueprint for the first shared staging environment

## Status

Accepted

## Context

Solara Hire needs two HTTPS web processes, a continuous Dramatiq worker, a
two-minute maintenance schedule, PostgreSQL, and Redis. The first staging
environment should exercise the production container images and release checks
without introducing Kubernetes or maintaining a virtual machine.

Railway's hosted cron has a five-minute minimum interval, which does not meet the
current two-minute task-delivery recovery target. Render represents every required
runtime responsibility in one infrastructure-as-code Blueprint and supports a
two-minute cron expression.

## Decision

Use `render.yaml` as the staging infrastructure definition. Deploy the API and
Next.js frontend as HTTPS web services, the Dramatiq process as a background
worker, maintenance as a cron job, and use Render Postgres and Key Value over the
private network.

The API runs Alembic as its single pre-deploy migration command. Platform-generated
URLs and datastore connection strings are referenced rather than copied. Random
internal secrets are platform-generated; identity and provider credentials are
declared with `sync: false` and entered only in Render. CI must pass before an
automatic deploy is eligible.

Render supplies a generic PostgreSQL connection URL, so the database boundary
normalizes only the generic `postgresql://` and legacy `postgres://` schemes to the
already-installed Psycopg 3 SQLAlchemy dialect. Explicit driver URLs are preserved.

## Consequences

- Staging has recurring infrastructure cost because workers and cron jobs do not
  have a free plan.
- The API has a public TLS hostname, but business endpoints remain token-protected;
  the browser-facing Next.js server uses the platform URL rather than a hardcoded
  address.
- Initial Auth0 callback and logout URLs must be added manually after Render assigns
  the frontend hostname.
- Production can reuse the topology after staging evidence exists, but sizing,
  custom domains, alerting, backup policy, and high availability remain separate
  production decisions.
