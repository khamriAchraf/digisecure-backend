# DigiSecure Backend

FastAPI backend for DigiSecure. The application uses PostgreSQL and reads its
local settings from `app/core/.env`.

## Run locally

### Prerequisites

- Python 3.12
- Poetry
- PostgreSQL 17 (a local installation, Docker, or a dedicated development database)

### 1. Install dependencies

From the repository root:

```powershell
poetry install --no-root
```

### 2. Configure PostgreSQL

For a disposable local database, start PostgreSQL with Docker:

```powershell
docker run --name digisecure-postgres `
  -e POSTGRES_USER=digisecure `
  -e POSTGRES_PASSWORD=digisecure_local `
  -e POSTGRES_DB=digisecure_dev `
  -p 5432:5432 `
  -d postgres:17
```

Alternatively, use an existing PostgreSQL development database. Do not point
the seeder at production.

Copy the example settings file and edit it to match your local database:

```powershell
Copy-Item docs\.env.example app\core\.env
```

`app/core/.env` is ignored by Git. Replace the example JWT secret and cron-job
API key with local-only values. The seeder needs permission to create tables,
functions, and triggers in the selected database. The example uses the local
Docker database above.

### 3. Create tables and seed baseline data

Run this only against a local or disposable development database:

```powershell
poetry run python -m app.utils.seed_db_schema --skip-fixtures
```

This creates the schema objects, roles, permissions, and compliance reference
data without demo assets or test users. To add demo fixtures, omit
`--skip-fixtures`. To create a local super-admin as part of seeding, pass
`--username`, `--email`, and `--password`; use disposable development
credentials.

### 4. Start the API

```powershell
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Check that the backend can reach PostgreSQL at
[http://localhost:8000/health](http://localhost:8000/health). Interactive API
documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

The local CORS configuration allows `http://localhost:3000` and
`http://localhost:8080`. Point a local frontend at
`http://localhost:8000/api/v1`.

For additional development notes, see
[docs/PREPARE_DEV_ENV.md](./docs/PREPARE_DEV_ENV.md) and
[docs/DATABASE_SETUP.md](./docs/DATABASE_SETUP.md).
