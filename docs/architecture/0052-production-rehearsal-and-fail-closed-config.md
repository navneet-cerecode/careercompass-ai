# ADR 0052: Production rehearsal and fail-closed configuration

- Status: Accepted
- Date: 2026-08-12

## Context

The portable runtime already used immutable non-root images and an explicit migration job,
but configuration drift could still produce a healthy-looking frontend that called its own
localhost instead of FastAPI. Auth0 domain, audience, and public-origin mismatches also failed
only after a user attempted to sign in.

## Decision

Use `SOLARAHIRE_API_URL` consistently for the server-only frontend-to-API route. Validate all
required backend, frontend, identity, and provider settings without printing values. Fail the
preflight when public origins, Auth0 hosts, or API audiences disagree.

Make API container health depend on PostgreSQL and Redis readiness, run long-lived containers
behind init processes with bounded graceful shutdown, and expose scheduled maintenance as an
explicit one-shot Compose profile. Keep backups, TLS termination, scheduling, alert delivery,
and image rollout platform-owned, with executable commands and acceptance criteria in the runbook.

Install only the dependencies reachable from the FastAPI/worker runtime, resolve Torch from its
CPU-only index, and use the broader frozen environment only as a version constraint. Bake the
semantic model at a fixed upstream revision and force offline model loading at runtime.
Self-host the editorial variable font from a pinned package so frontend builds and page rendering
do not depend on a third-party font request.

## Consequences

- Containerized frontend requests reach the internal API service by its configured name.
- Common authentication drift is rejected before deployment rather than during sign-in.
- Dependency loss is visible through container health and rollout gates.
- The same immutable API image runs migrations, workers, and maintenance.
- Semantic scoring no longer requires model-registry egress during a user request.
- Database downgrade and restore remain explicit incident decisions, never automatic startup work.
