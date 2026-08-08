# 0032 — Privacy-bounded observability

Status: accepted

## Decision

Separate operational request telemetry from product analytics. Every API response
receives a correlation ID and every request produces one structured record using
the HTTP method, matched route template, status, and duration. Query strings,
request bodies, authorization headers, IP addresses, user agents, and concrete
resource identifiers are excluded.

Product analytics uses a typed, provider-neutral sink with an event-specific
property allowlist. It is disabled by default. When enabled, authenticated actors
are included only when a dedicated analytics salt is configured, and the internal
user ID is transformed with HMAC-SHA256 before emission.

Resume content, filenames, skills, job descriptions, job identifiers, application
notes, emails, names, and search text are not analytics properties. A future
analytics provider must implement the same sink boundary rather than receiving
arbitrary application payloads.
