# ADR 0044: Relevance-gated The Muse provider

- Status: Accepted
- Date: 2026-08-11

## Context

The Muse exposes broad technical and non-technical job categories, but its public API still has no
general keyword parameter. Live checks also showed that an India location query can return mostly
remote or overseas listings. Trusting the upstream filters would weaken recommendation relevance.

The API now uses `https://www.themuse.com/api/public`, requires application registration for real
use, applies rate limits, and requires Muse content to link back to The Muse.

## Decision

Add The Muse through the existing provider contract, disabled until `THE_MUSE_API_KEY` is present.
Map only recognized role families to documented Muse categories. After each response, require a
matching functional title term and the requested location. Accept remote-only listings only when
the user explicitly requests remote work.

Normalize accepted listings into the canonical `Job` model and use the Muse landing page for both
the source and application URL. Display linked provider attribution in every existing job surface.
Unmapped role families return no results without calling the API.

## Consequences

- Solara Hire gains additional non-technical coverage without treating provider-side filtering as
  sufficient evidence of relevance.
- The adapter intentionally favors precision over recall.
- Extending the role-to-category map is a reviewed code change rather than an opaque inference.
- Production enablement requires a registered Muse application and continued compliance with its
  API terms and rate limits.
