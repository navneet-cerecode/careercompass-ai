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

An external analytics provider must implement the `AnalyticsSink` boundary. It
must not receive arbitrary request objects or domain models. Provider outages
must remain non-blocking for product operations, and the sink failure log must
not include event properties or actor identifiers.
