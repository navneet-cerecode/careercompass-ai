# Observability operations

## Request correlation

The Next.js server generates an `X-Request-ID` for proxied API calls. FastAPI
accepts a conservative alphanumeric request ID, generates one when necessary,
and returns it on the response. Request records contain only:

- request ID
- HTTP method
- matched route template
- response status
- elapsed milliseconds

Concrete resource IDs, query strings, bodies, authorization headers, IP
addresses, and user agents are intentionally excluded. Configure the production
log collector to parse the JSON message and preserve `X-Request-ID` when filing
support incidents.

## Product events

Product analytics is disabled by default. Set `ANALYTICS_ENABLED=true` only
after the privacy policy and production log destination are approved. Set
`ANALYTICS_IDENTITY_SALT` through the secret manager to a dedicated random value
of at least 32 characters when pseudonymous journey analysis is required.

The initial event contract covers:

- resume parsing success
- job-search requests
- recommendation generation
- saved jobs
- application tracking starts and status changes
- billing summary views

Every event has an event-specific property and value allowlist. Raw user IDs are
never emitted; authenticated actors are HMAC-SHA256 pseudonyms only when the salt
is present. Resume content, filenames, skills, search text, locations, job data,
notes, names, and emails are excluded.

Changing the analytics salt breaks historical actor continuity. Treat rotation
as a deliberate privacy event, document it, and do not retain the prior salt in
application configuration.

## Provider integration

Each observed provider search emits a `provider_search` JSON record containing only the provider
identifier, outcome, elapsed milliseconds, attempts, returned-job count, and sanitized failure code.
Search text, location, job payloads, resume evidence, credentials, and exception messages are not
included. Use these records for latency percentiles and source-specific availability alerts.

An external analytics provider must implement the `AnalyticsSink` boundary. It
must not receive arbitrary request objects or domain models. Provider outages
must remain non-blocking for product operations, and the sink failure log must
not include event properties or actor identifiers.

## Starting alert thresholds

Tune these after production traffic establishes a stable baseline. They are initial
operator signals, not contractual service-level objectives:

| Signal | Starting condition | Response |
| --- | --- | --- |
| API readiness | Any failure for 2 consecutive minutes | Page the on-call operator; check PostgreSQL and Redis first. |
| API server errors | More than 1% HTTP 5xx for 5 minutes | Page and correlate by route template and request ID. |
| API latency | p95 above 1 second for 10 minutes | Investigate saturation, database waits, and downstream latency. |
| Worker backlog | Oldest queued task above 5 minutes | Check worker health, Redis delivery, and database pool pressure. |
| Worker failures | More than 5% terminal failures for 10 minutes | Inspect sanitized error codes; never attach task payloads. |
| Provider health | One source unavailable in 3 consecutive search windows | Warn; inspect that provider's latency records. |
| Authentication | Identity-provider-unavailable responses for 2 minutes | Page; distinguish provider failure from invalid-token 401 responses. |

Alert payloads may contain request IDs, route templates, provider identifiers, statuses,
durations, counts, and sanitized error codes only. Do not forward tokens, query strings,
resume data, job payloads, emails, notes, or exception messages.
