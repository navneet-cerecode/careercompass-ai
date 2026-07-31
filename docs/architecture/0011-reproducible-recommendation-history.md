# ADR 0011: Persist Reproducible Search and Recommendation History

- Status: Accepted
- Date: 2026-08-01

## Decision

- Persist owner-scoped search queries, filters, provider outcomes, and ordered job results.
- Persist the exact resume version and durable job used for every recommendation.
- Store score components, matched and missing skills, confidence, rank, and algorithm version.
- Reconstruct recommendation domain models through repositories rather than returning ORM rows.
- Keep unauthenticated public search and recommendation requests detached from user history.

This preserves explainability and makes historical recommendations reproducible after scoring
algorithms change, without silently assigning anonymous activity to a user.
