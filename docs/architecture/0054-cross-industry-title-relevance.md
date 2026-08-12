# ADR 0054: Conservative cross-industry title relevance

- Status: Accepted
- Date: 2026-08-13

## Context

Aggregators sometimes match a search term in the employer name or description while returning a
published title from another career lane. Resume similarity alone cannot make an unrelated role a
valid recommendation. Requiring literal title equality would also discard legitimate equivalents
such as `AI` and `Machine Learning`, `HR` and `Human Resources`, or `Nurse` and `Registered Nurse`.

## Decision

At the normalized quality boundary, require every meaningful searched role concept to appear in
the published title. Ignore seniority and generic role modifiers, and use only a small curated set
of high-confidence career aliases. Cover both technical and non-technical examples in the contract
tests. Treat a mismatch as a quality rejection, separate from provider availability and candidate
match scoring.

Do not infer relevance from employer names or descriptions. Do not use resume content in this
gate. Expand aliases only with reviewed examples and paired false-positive tests.

## Consequences

- Aggregator records from unrelated career lanes do not enter ranking or persistence.
- Common title variants remain discoverable without an AI call or hidden scoring rule.
- The behavior is deterministic, inexpensive, explainable, and provider-neutral.
- Novel title equivalents may be conservatively omitted until the alias contract is reviewed.
