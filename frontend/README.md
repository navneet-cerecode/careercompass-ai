# Solara Hire frontend

The canonical Next.js App Router interface for Solara Hire. Streamlit remains available as
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

For signed-in development, configure the server-only Auth0 values documented in `.env.example`.
The Auth0 application must be a Regular Web Application with
`http://localhost:3000/auth/callback` registered as an allowed callback and
`urn:solarahire:api` requested as the audience. Access tokens remain in the encrypted server
session and are forwarded to FastAPI only by same-origin route handlers.

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

`SOLARAHIRE_API_URL` and `SOLARAHIRE_SITE_URL` are server-only configuration. Never place
API keys, database credentials, or provider secrets in a `NEXT_PUBLIC_*` variable.

The complete parity and rollback contract is documented in
`../docs/frontend-cutover.md`.
