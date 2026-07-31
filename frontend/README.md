# CareerCompass AI frontend

The additive Next.js App Router interface for CareerCompass AI. Streamlit remains available until
the Phase 4 feature-parity gate is complete.

## Local development

Run FastAPI from the repository root:

```powershell
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
