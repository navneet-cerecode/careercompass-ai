# Database migrations

Run migrations only with an explicit `DATABASE_URL`:

```powershell
alembic upgrade head
```

Migration files must support downgrade until a later ADR explicitly documents an irreversible
data migration.

Use a dedicated disposable database for the real PostgreSQL gate:

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://user:password@localhost/careercompass_test"
python -m pytest -m postgres
```

The integration test downgrades that database to `base` before and after the gate. Never point
`TEST_DATABASE_URL` at a development, staging, or production database containing useful data.
