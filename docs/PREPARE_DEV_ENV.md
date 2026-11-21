# Local Development Setup

The quick start in the [README](../README.md) covers installing dependencies,
configuring PostgreSQL, seeding a local database, and starting the API.

## Requirements

- Python 3.12
- Poetry
- PostgreSQL 17
- Docker only if you want to run PostgreSQL in a container

## Environment configuration

The application loads its settings from `app/core/.env`. Create it from the
tracked, secret-free template:

```powershell
Copy-Item docs\.env.example app\core\.env
```

Edit the database settings and replace the example JWT secret and
`SYSTEM_CRONJOB_API_KEY` with local-only values. Never commit `app/core/.env`.
The required database settings are `DB_HOST`, `DB_PORT`, `DB_USER`,
`DB_PASSWORD`, `DB_NAME`, and `DB_SCHEMA`. `JWT_SECRET`, `JWT_ALGORITHM`,
`JWT_EXPIRATION_MINUTES`, `JWT_REFRESH_EXPIRATION_DAYS`,
`EVENT_NOTIFICATION_CALLBACK_URL`, and `SYSTEM_CRONJOB_API_KEY` are also
required.

Optional settings such as `EMAIL_SERVICE_URL`, `PASSWORD_RESET_URL`,
`PASSWORD_RESET_TOKEN_EXPIRE_MINUTES`, `DEBUG`, and `GEOLITE2_DB_PATH` have
defaults in `app/core/config.py`. GeoIP lookup requires a separately downloaded
MaxMind GeoLite2 City database; without it, the application logs a warning.
See [docs/GEOLOCATION.md](./GEOLOCATION.md) for details.

## Install and run

From the repository root:

```powershell
poetry install --no-root
poetry run python -m app.utils.seed_db_schema --skip-fixtures
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The seed command creates missing tables and baseline role, permission, and
compliance data. It requires a development database and a database user with
permission to create the database if absent, plus its schema objects,
functions, and triggers. Run it only against a local or disposable development
database. Add `--username`, `--email`, and `--password` to create a
super-admin, or omit `--skip-fixtures` to add demo data.

The legacy `seed_db.sh` script is not suitable for setup: it ignores
super-admin arguments and creates the hard-coded `admin` / `admin` account.
Use the Python module command above instead.

The API listens on `http://localhost:8000`; use `/health` to check database
connectivity and `/docs` for the interactive API documentation.

## PostgreSQL auditing

For a PostgreSQL environment with `pgaudit`, see
[DATABASE_SETUP.md](./DATABASE_SETUP.md). A local `pgaudit` setup is optional
for starting the API.

## Tests

Install the project's development dependencies with `poetry install --no-root`.
Configure the test settings in `app/core/.env.test` before running tests:

```powershell
poetry run pytest
```

Keep test settings and test databases separate from development and production
credentials and data.
