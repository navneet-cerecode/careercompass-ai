# ADR 0049: Observed provider reliability

- Status: Accepted
- Date: 2026-08-12

## Context

Job discovery isolates provider failures, but retry behavior previously existed only inside
JSearch and every API failure was reduced to `provider_failed`. Separate live health probes would
consume provider quota and could report a source healthy immediately before a real search fails.

## Decision

Retry transient failures once at the shared discovery boundary. Retry timeouts, connection errors,
HTTP 408, HTTP 429, and selected 5xx responses. Honor numeric `Retry-After` values for rate limits,
but cap every delay at two seconds. Do not retry invalid payloads, configuration failures, or other
permanent errors.

Persist and return only sanitized failure codes, attempt counts, and observed health status. Treat
successful providers as reached and classify failed providers as degraded or unavailable from the
actual search attempt. Remove JSearch's adapter-specific retry loop.

## Consequences

- Every provider receives the same bounded transient-failure policy.
- Partial results remain available when one source exhausts its retry.
- Synchronous and background search responses retain the same failure detail.
- No proactive provider probe consumes quota or claims health beyond an observed search.
