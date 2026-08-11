# Solara Hire

Solara Hire is an explainable job discovery and resume-matching application. The canonical
interface is the Next.js workspace in `frontend/`, backed by FastAPI, Python application
services, LangGraph orchestration, and PostgreSQL.

The repository is being migrated incrementally toward a production SaaS architecture. The
former Streamlit interface remains available as a compatibility fallback and is not removed by
the frontend cutover.

## Current capabilities

- Upload PDF, DOCX, or TXT resumes.
- Extract contact details, experience evidence, and cross-industry skills for user review.
- Discover jobs from configured broad-market aggregators and direct career sources.
- Normalize results into the current `Job` model and remove simple duplicates.
- Rank jobs using skill-overlap and semantic-similarity signals.
- Request an optional Groq-generated recruiter analysis.
- Save jobs and track applications in authenticated, owner-scoped workspaces.
- Create versioned factual tailoring drafts for entitled accounts.
- Compare original, suggested, and accepted resume ordering before approval.
- Export user-verified tailored resumes as PDF or DOCX.
- Draft concise cover letters from verified resume evidence and target-job facts.
- Edit, version, fact-check, and export approved cover letters as PDF or DOCX.
- Assemble review-first application packets before recording an external submission.
- Prepare for interviews with role questions, resume evidence prompts, and user-authored notes.
- Compare reviewed resume skills with explicit requirements observed across searched, saved, and
  tracked roles using disclosed exact or curated high-confidence aliases, without presenting the
  sample as market-wide demand.

The built-in provider set includes Adzuna, Arbeitnow, JSearch, The Muse, NVIDIA Workday, and
curated Greenhouse, SmartRecruiters, and Ashby employer boards.
Adzuna and The Muse are enabled only when their credentials are configured. Arbeitnow serves its
supported Germany and UK feeds. The Muse locally enforces title and location relevance because its
public API has no general keyword filter.
Greenhouse currently covers Appian and Blenheim Chalcot India; SmartRecruiters covers Bosch Group
and KredX India; Ashby covers Aspora and Riveron. These integrations are discovery-only and
perform no application submission.

## Requirements

- Python 3.13
- Node.js 24
- Docker Desktop or PostgreSQL 16
- A Groq API key
- A RapidAPI key with access to JSearch
- Optional Adzuna application ID and key for broad-market coverage

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

Set one stable `TASK_TOKEN_SECRET` of at least 32 random bytes in `.env`. Every API process must use
the same value so background-search polling tokens remain valid across restarts. Generate a value
locally with PowerShell, copy it into the ignored `.env`, and clear it from the terminal afterward:

```powershell
$secretBytes = New-Object byte[] 48
$random = [Security.Cryptography.RandomNumberGenerator]::Create()
$random.GetBytes($secretBytes)
[Convert]::ToBase64String($secretBytes)
$random.Dispose()
Remove-Variable secretBytes, random
```

Authentication uses provider-neutral OIDC access tokens. Configure `AUTH_ISSUER`,
`AUTH_AUDIENCE`, and `AUTH_JWKS_URL` together when enabling signed-in APIs. Solara Hire stores
external issuer/subject links but never passwords or provider tokens. The canonical Next.js
frontend uses an encrypted, HTTP-only Auth0 session and forwards access tokens to FastAPI only
from server-side route handlers.

The public product name is Solara Hire. Legacy database, Docker-volume, queue, and Python-facade
identifiers retain the CareerCompass codename until they can be migrated without breaking local
data or compatibility.

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

The worker registers durable job discovery, bounded maintenance, and the internal `system.probe`
verification actor. Redis messages carry identifiers only; PostgreSQL owns task inputs, results,
and lifecycle state.

Trigger one maintenance cycle from another terminal:

```powershell
$env:REDIS_URL = "redis://127.0.0.1:6379/0"
.\venv\Scripts\python.exe -m workers.enqueue_maintenance
```

Production must schedule that command at least once per `TASK_DELIVERY_RETRY_SECONDS`.

Run FastAPI from the repository root:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://careercompass:careercompass@127.0.0.1:5432/careercompass"
$env:REDIS_URL = "redis://127.0.0.1:6379/0"
$env:TASK_TOKEN_SECRET = "the-same-private-value-stored-in-your-env-file"
.\venv\Scripts\python.exe -m uvicorn api.main:app --reload
```

In a second terminal, run Next.js:

```powershell
Set-Location frontend
Copy-Item .env.example .env.local
npm.cmd run dev
```

Open `http://localhost:3000/workspace`. The frontend uses the server-only
`SOLARAHIRE_API_URL` setting to reach FastAPI. API keys and database credentials must never
be placed in a `NEXT_PUBLIC_*` variable.

In a third terminal, verify the running cutover surface:

```powershell
.\venv\Scripts\python.exe scripts\smoke_frontend.py
```

This gate also verifies the configured public OIDC signing-key endpoint. Do not continue local
testing if that check fails: the UI can still load, but signed-in API requests cannot be verified.

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

Discovery publication uses a transactional outbox. Heartbeats, stale-worker recovery, bounded
redelivery, cooperative cancellation, queue expiry, and terminal-history retention are handled
by scheduled maintenance. See `docs/operations/background-tasks.md`.

Verified bearer identities provision credential-free user profiles through `(issuer, subject)`.
Authenticated resume uploads become immutable owner-scoped versions, and authenticated discovery
tasks require the same owner for polling and cancellation. Email collisions require explicit
future account linking rather than automatic merging.

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
`Job` model. The active adapters are `AdzunaProvider`, `ArbeitnowProvider`, `JSearchProvider`,
`TheMuseProvider`, and `WorkdayProvider`; credential and geography checks determine which
participate in a search.

JSearch uses `job_uid` as its stable provider identity and retains `job_id` only as a compatibility
fallback. Provider outages produce explicit partial-coverage results rather than failing the
complete search. Displayed Adzuna and Muse listings carry their required linked attribution.

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

The current foundation includes durable task records, Redis worker actors, authenticated ownership,
provider-neutral subscriptions, and privacy-bounded request and product telemetry. Payment-provider
checkout, external analytics delivery, production deployment, and S3-compatible object storage
remain incremental follow-on work. Streamlit removal requires the separate gate in
`docs/frontend-cutover.md`.

## Security and privacy

Resumes contain sensitive personal information. Local uploads are parsed through a temporary
file that is deleted immediately after parsing. Do not add raw resume contents or API responses
to logs. Use synthetic data for tests.

Report suspected credential exposure immediately and rotate the affected key before continuing
development.

Operational telemetry deliberately excludes request bodies, query strings, raw resource IDs, and
personal profile data. Deployment guidance and the approved product-event contract are documented
in `docs/operations/observability.md`.
