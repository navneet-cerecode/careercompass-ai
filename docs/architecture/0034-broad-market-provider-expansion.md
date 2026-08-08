# 0034 — Expand broad-market discovery without weakening relevance

Status: accepted

## Context

The first production adapters—JSearch and NVIDIA Workday—proved the provider boundary but leaned
toward technical roles and a single company career site. Solara Hire must support candidates in
operations, healthcare, administration, sales, hospitality, finance, retail, and other career
lanes without allowing provider-specific payloads or irrelevant geography into recommendations.

Provider behavior also changes independently of Solara Hire. JSearch changed its identifier
contract so search-scoped `job_id` values are no longer stable, and live provider outages can
return transient 429 or 5xx responses.

## Decision

- Add Adzuna as a credential-gated broad-market aggregator using its country-specific search API.
- Add Arbeitnow as a keyless provider only for its supported Germany and UK feeds.
- Keep NVIDIA Workday as a direct-career source, but locally exclude results outside the user's
  requested location because its configured search endpoint does not apply that preference.
- Use JSearch `job_uid` as the stable external identity, with `job_id` as a legacy fallback.
- Match durable provider-source records by provider and stable external ID before falling back to
  source URL, allowing redirect URLs to refresh without creating another source record.
- Retry bounded JSearch 429, 500, 502, 503, and 504 responses. Exhausted retries remain an explicit
  partial provider failure and never discard jobs returned by healthy providers.
- Display linked "Jobs by Adzuna" attribution on every recommendation, saved job, and tracked
  application sourced from Adzuna.
- Defer The Muse adapter. Its public jobs endpoint is healthy but does not offer general keyword
  search, and its tested India location query returned predominantly global or US listings. It
  should be reconsidered only with a registered application and a relevance-preserving query plan.

## Consequences

Search coverage is broader and includes non-technical roles without pretending every provider
supports every geography. Provider counts are configuration-dependent, partial failures name the
unavailable source, and results contain only jobs that passed each adapter's implemented filters.

Adzuna production use remains subject to its API terms and commercial licensing. Live provider
checks remain manual operational verification; automated tests use mocked payloads and consume no
external quota.
