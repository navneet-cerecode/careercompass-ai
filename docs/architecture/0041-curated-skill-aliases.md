# ADR 0041: Curated skill aliases with explicit confidence

- Status: Accepted
- Date: 2026-08-09

## Context

Equivalent skills often arrive with different labels, such as `MS Excel` and `Microsoft Excel`,
or an acronym and its expansion. Exact case-insensitive matching misses those relationships.
Fuzzy text similarity, stemming, or an unconstrained language-model decision could also merge
related but materially different capabilities, especially across non-technical careers.

## Decision

Use a small, version-controlled allow-list of high-confidence aliases for the observed-role skill
intelligence comparison. The initial list covers common office, operations, human-resources,
marketing, healthcare, and technology abbreviations and product names.

Every supported comparison reports either `exact` or `curated_high` confidence. Curated matches
also return the original resume and provider terms so the user can see why they were joined.
Unlisted terms remain distinct; for example, customer service is not silently treated as customer
support, and inventory management is not silently treated as inventory control.

The alias layer affects comparison only. It does not rewrite the reviewed resume, mutate stored
job requirements, or infer that two unlisted skills are equivalent.

## Consequences

- Equivalent high-confidence labels produce more useful comparisons without paid model calls.
- The behavior is deterministic, reviewable, cross-industry, and covered by contract tests.
- New aliases require an explicit code review rather than emerging from opaque similarity scores.
- A governed external taxonomy can replace the allow-list when coverage and maintenance needs
  justify the additional system.
