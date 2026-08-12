# ADR 0053: Objective normalized-job quality gate

- Status: Accepted
- Date: 2026-08-13

## Context

Provider APIs can return structurally valid records that are unusable for evidence-based ranking,
including placeholder identities, empty descriptions, and synthetic fixtures. Allowing those jobs
into the durable catalog weakens recommendations and makes provider health counts misleading.
Provider-specific semantic filtering already exists for selected ATS adapters, but applying an
untested global title matcher would risk excluding valid technical and non-technical careers.

## Decision

Apply a small, provider-neutral quality gate after every adapter has produced the canonical `Job`
model and before deduplication or persistence. Reject only objective defects: placeholder title,
company, or location values; empty descriptions; and unambiguous synthetic company fixtures.

Keep successful providers successful when some or all records are rejected. Record privacy-safe,
provider-scoped rejection counts in the discovery result and structured provider-search log. Do
not log job contents, search terms, resume data, URLs, or identifiers. Leave semantic relevance to
the explainable ranking path until a cross-industry relevance contract is designed and tested.

## Consequences

- Unusable provider records cannot pollute the catalog or recommendation history.
- Operators can distinguish healthy empty results from quality-gate rejection without personal
  data in telemetry.
- Provider availability and result quality remain separate signals.
- Future relevance tuning can build on observed rejection data instead of speculative title rules.
