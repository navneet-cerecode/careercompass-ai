# CareerCompass AI

CareerCompass AI is an explainable job discovery and resume-matching application. The canonical
interface is the Next.js workspace in `frontend/`, backed by FastAPI, Python application
services, LangGraph orchestration, and PostgreSQL.

The repository is being migrated incrementally toward a production SaaS architecture. The
former Streamlit interface remains available as a compatibility fallback and is not removed by
the frontend cutover.

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
- Node.js 24
- Docker Desktop or PostgreSQL 16
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
python -m pip install -r requirements-worker.txt
python -m pip install -r requirements-dev.txt
```

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Populate the required keys in `.env`. Never commit that file or paste credentials into tests,
logs, screenshots, or issue reports.

## Run the canonical web product

Install the complete development dependency layers:

```powershell
python -m pip install -r requirements-worker.txt
python -m pip install -r requirements-dev.txt
Set-Location frontend
npm.cmd install
Set-Location ..
```

Start the repository-managed PostgreSQL and Redis services, then apply migrations:

```powershell
docker compose up -d postgres redis
$env:DATABASE_URL = "postgresql+psycopg://careercompass:careercompass@127.0.0.1:5432/careercompass"
.\venv\Scripts\python.exe -m alembic upgrade head
```

The Docker password is a local-development default only. Never reuse it in staging or
production. If PostgreSQL is already running, point `DATABASE_URL` at that development database
instead of starting a second service.

Redis is the Phase 5 background-job broker. Its local port is bound to loopback, and its data
volume is for development convenience only. PostgreSQL remains the durable source of truth.

Start the Phase 5 worker runtime in a separate terminal:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://careercompass:careercompass@127.0.0.1:5432/careercompass"
$env:REDIS_URL = "redis://127.0.0.1:6379/0"
.\venv\Scripts\python.exe -m dramatiq workers.entrypoint --processes 1 --threads 4
```

The only registered actor is currently an internal `system.probe` operation used to verify
delivery and lifecycle behavior. It calls no job provider or AI model and has no public API
endpoint.

Run FastAPI from the repository root:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://careercompass:careercompass@127.0.0.1:5432/careercompass"
.\venv\Scripts\python.exe -m uvicorn api.main:app --reload
```

In a second terminal, run Next.js:

```powershell
Set-Location frontend
Copy-Item .env.example .env.local
npm.cmd run dev
```

Open `http://localhost:3000/workspace`. The frontend uses the server-only
`CAREERCOMPASS_API_URL` setting to reach FastAPI. API keys and database credentials must never
be placed in a `NEXT_PUBLIC_*` variable.

In a third terminal, verify the running cutover surface:

```powershell
.\venv\Scripts\python.exe scripts\smoke_frontend.py
```

FastAPI remains the source of truth for HTTP contracts. Regenerate the committed OpenAPI
document and TypeScript declarations after changing an API schema from `frontend/`:

```powershell
npm.cmd run contract:generate
```

## Streamlit compatibility fallback

The root `app.py` remains available for rollback and the legacy Groq AI Inspector:

```powershell
.\venv\Scripts\python.exe -m streamlit run app.py
```

New interface work belongs in Next.js. See `docs/frontend-cutover.md` for the parity matrix and
the explicit removal gate.

## Database migrations

Persistence uses SQLAlchemy, Psycopg, and Alembic. Install the database dependency layer:

```powershell
python -m pip install -r requirements-db.txt
```

Set `DATABASE_URL` locally, then apply migrations:

```powershell
alembic upgrade head
```

Database construction is lazy, so Streamlit and FastAPI can still start without database
credentials until a persistence-backed operation is used.

Job search now upserts canonical jobs and separate provider-source records. Search responses use
durable database IDs, allowing job-detail and recommendation requests to survive process restarts
and work across API workers.

Background work has a durable PostgreSQL lifecycle record with owner-ready scoping, hashed
idempotency fingerprints, bounded attempts, and safe machine-readable failure codes. Task rows
contain identifiers and lifecycle metadata only; Redis remains the delivery broker and does not
replace PostgreSQL task history.

## Verification

Run the offline test suite:

```powershell
python -m pytest -m "not postgres and not redis"
```

With the repository Redis service running, verify the worker broker:

```powershell
$env:TEST_REDIS_URL = "redis://127.0.0.1:6379/15"
python -m pytest -m redis
```

Run lint and formatting checks for tests you change:

```powershell
ruff check tests
ruff format --check tests
```

The CI workflow contains the authoritative expanded boundary for migrated production modules.
It also starts a disposable PostgreSQL 16 service and runs the migration and persistence
integration gate separately from offline tests.

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
Next.js web interface
  -> narrow server-side route handlers
     -> versioned FastAPI boundary
        -> resume parsing and extraction
        -> LangGraph job discovery
           -> provider adapters
           -> normalization and deduplication
        -> PostgreSQL job catalog
        -> PostgreSQL background-task lifecycle
        -> recommendation signals and score fusion

Streamlit compatibility fallback
  -> CareerCompass facade
     -> shared Python application services
     -> optional legacy Groq analysis
```

The remaining long-term direction adds durable task records and worker actors on the Redis broker,
authenticated ownership, subscription billing, production observability, and S3-compatible
object storage. Migration remains incremental; Streamlit removal requires the separate gate in
`docs/frontend-cutover.md`.

## Security and privacy

Resumes contain sensitive personal information. Local uploads are parsed through a temporary
file that is deleted immediately after parsing. Do not add raw resume contents or API responses
to logs. Use synthetic data for tests.

Report suspected credential exposure immediately and rotate the affected key before continuing
development.
