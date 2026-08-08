# 0033 — Portable production runtime

Status: accepted

## Decision

Ship separate non-root containers for the FastAPI/worker runtime and the standalone
Next.js frontend. Use one immutable Python image for API, migrations, and workers so
the domain code and migration graph cannot drift across a release. Database migration
is a one-shot prerequisite, not an API startup side effect.

Production settings fail closed when persistence, broker, task capability, verified
identity, HTTPS identity endpoints, or explicit allowed hosts are missing. Browser and
API responses use a common baseline of anti-sniffing, framing, referrer, permissions,
and transport-security headers appropriate to their boundary.

Deployment remains vendor-neutral. PostgreSQL, Redis, TLS termination, secret storage,
scheduling, backups, alerting, and image rollout are platform responsibilities recorded
in the production runbook rather than embedded as provider-specific application code.
