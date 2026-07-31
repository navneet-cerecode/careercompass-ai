# ADR 0004: Stabilize Resume and Ranking Boundaries

- Status: Accepted
- Date: 2026-08-01

## Context

Resume collection fields used mutable class-level defaults, blank source text could reach the
extractor, and semantic matching omitted the original resume text. Skill title-casing also
damaged established technology names such as SQL and PyTorch. The Streamlit page constructed
the facade on every rerun, and the repository's root entry point was empty.

## Decision

- Reject blank candidate names and blank resume source text at the domain boundary.
- Use Pydantic default factories for resume collections.
- Reject parser output that contains no extractable text.
- Include the source resume text in the semantic-matching input.
- Normalize a bounded set of established technology names without inventing resume facts.
- Cache the `CareerCompass` facade as a Streamlit resource.
- Use root `app.py` as the canonical Streamlit entry point while retaining `ui/app.py`
  compatibility.

## Consequences

The ranking engine now receives the candidate's real resume content instead of only partially
populated structured fields. Empty or image-only uploads fail with a clear validation error
rather than producing a misleading profile. Structured experience, education, and project
models remain future work and are not inferred from unverified text in this phase.
