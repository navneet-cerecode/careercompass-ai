# CareerCompass AI frontend

The canonical Next.js App Router interface for CareerCompass AI. Streamlit remains available as
an explicitly documented compatibility fallback.

## Local development

Start PostgreSQL and run migrations from the repository root:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://careercompass:careercompass@127.0.0.1:5432/careercompass"
docker compose up -d postgres
.\venv\Scripts\python.exe -m alembic upgrade head
```

Then run FastAPI:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://careercompass:careercompass@127.0.0.1:5432/careercompass"
.\venv\Scripts\python.exe -m uvicorn api.main:app --reload
```

Then start this frontend:

```powershell
Copy-Item .env.example .env.local
npm.cmd install
npm.cmd run contract:generate
npm.cmd run dev
```

Open `http://localhost:3000`.

From the repository root, verify the running web boundary:

```powershell
.\venv\Scripts\python.exe scripts\smoke_frontend.py
```

## Quality gates

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build
npm.cmd audit --audit-level=high
```

`CAREERCOMPASS_API_URL` and `CAREERCOMPASS_SITE_URL` are server-only configuration. Never place
API keys, database credentials, or provider secrets in a `NEXT_PUBLIC_*` variable.

The complete parity and rollback contract is documented in
`../docs/frontend-cutover.md`.
