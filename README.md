# CareerCompass AI

CareerCompass AI is an early-stage job discovery and resume-matching prototype. The current
interface is built with Streamlit, while job discovery, normalization, recommendation signals,
and LangGraph orchestration live in Python service modules.

The repository is being migrated incrementally toward a production SaaS architecture. The
current milestone intentionally preserves the prototype while establishing documentation,
offline tests, and basic safety controls.

## Current capabilities

- Upload PDF, DOCX, or TXT resumes.
- Extract contact details and a limited set of technical skills.
- Discover jobs from the currently active JSearch and NVIDIA Workday providers.
- Normalize results into the current `Job` model and remove simple duplicates.
- Rank jobs using skill-overlap and semantic-similarity signals.
- Request an optional Groq-generated recruiter analysis.

Adzuna, Arbeitnow, The Muse, Greenhouse, SmartRecruiters, and Ashby are part of the product
roadmap but are not active provider implementations in this repository yet.

## Requirements

- Python 3.13
- A Groq API key
- A RapidAPI key with access to JSearch

## Local setup

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install runtime and development dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Populate the required keys in `.env`. Never commit that file or paste credentials into tests,
logs, screenshots, or issue reports.

## Run the prototype

The canonical Streamlit entry point is the root `app.py`:

```powershell
streamlit run app.py
```

`ui/app.py` remains executable during the migration for backwards compatibility.

## Verification

Run the offline test suite:

```powershell
python -m pytest
```

Run lint and formatting checks for tests you change:

```powershell
ruff check tests
ruff format --check tests
```

The CI workflow contains the authoritative expanded boundary for migrated production modules.

The automated suite must not call live job providers, Groq, or embedding-model download
endpoints. Provider and workflow behavior is tested with fixtures and mocks.

## Domain contracts

Recommendation scoring uses three distinct responsibilities:

- `ScoreComponent` represents one bounded, explainable scoring signal.
- `MatchAssessment` represents the versioned evaluation of one candidate resume against one job.
- `JobRecommendation` is the ranked presentation record backed by a `MatchAssessment`.

The former `SignalResult`, `MatchResult`, and `RecommendationResult` imports remain available as
temporary compatibility aliases. New production code should use the canonical model names.
The decision and migration rules are recorded in
`docs/architecture/0001-recommendation-domain-models.md`.

## Provider contracts

`services/job_discovery/providers` is the canonical provider package. Providers accept a typed
`JobSearchQuery`, declare implemented capabilities, and normalize raw payloads into the shared
`Job` model. `JSearchProvider` and `WorkdayProvider` are the active production adapters.

The former `APIProvider`, positional `search(role, location)`, and duplicate provider-base import
remain as compatibility adapters. The provider decision is recorded in
`docs/architecture/0002-unified-job-provider-contract.md`.

## Workflow boundaries

The Streamlit search uses a discovery-only LangGraph workflow. Batch assessment, sorting, and rank
assignment are owned by `RecommendationService`, not the UI. A separate resume-aware LangGraph
workflow is available for flows that genuinely need discovery and assessment in one graph.

The former hard-coded candidate score is no longer part of the production path. The orchestration
decision is recorded in
`docs/architecture/0003-workflow-and-recommendation-orchestration.md`.

Resume inputs reject empty extracted text, semantic matching includes the original resume content,
and known technology names retain canonical casing. These boundary decisions are recorded in
`docs/architecture/0004-resume-ranking-boundaries.md`.

## Current architecture

```text
Streamlit UI
  -> CareerCompass facade
     -> resume parsing and extraction
     -> LangGraph job discovery
        -> provider adapters
        -> normalization and deduplication
     -> recommendation signals and score fusion
     -> optional Groq analysis
```

The long-term direction is a Next.js frontend, FastAPI backend, PostgreSQL persistence, Redis
and background workers, and S3-compatible object storage. Migration will remain incremental;
Streamlit will not be removed until its replacement reaches agreed feature parity.

## Security and privacy

Resumes contain sensitive personal information. Local uploads are parsed through a temporary
file that is deleted immediately after parsing. Do not add raw resume contents or API responses
to logs. Use synthetic data for tests.

Report suspected credential exposure immediately and rotate the affected key before continuing
development.
