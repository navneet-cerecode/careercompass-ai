# ADR 0042: Owner-scoped role history context

- Status: Accepted
- Date: 2026-08-10

## Context

Observed-role skill intelligence needs enough context for a user to understand which career
directions and time period shaped the comparison. Provider posting dates are incomplete and do
not describe when a role became part of a user's own evidence set.

## Decision

Build the comparison window from existing owner-scoped history. Successful job-discovery tasks
use their creation and latest update timestamps. Saved jobs and tracked applications use their
creation timestamps when they add roles that are not already represented by search history.

Group search results under the user's latest search intent for that role. Saved or tracked roles
without search history fall back to their exact job title. Freshness buckets describe when each
distinct role was last observed: the last 7 days, 8–30 days, or more than 30 days ago.

The API and interface explicitly label these values as Solara Hire history. They are not employer
posting dates, job availability guarantees, or market-wide trend measurements.

## Consequences

- Users can see the evidence window and career directions behind their skill comparison.
- The feature remains deterministic, owner-scoped, and requires no new persistence or provider
  calls.
- Repeated searches update a role's freshness and latest search-intent cluster.
- A future market-intelligence product will need a separate provider-backed dataset and must not
  reinterpret these user-history fields.
