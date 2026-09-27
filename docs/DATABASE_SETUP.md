# Database Setup

The backend needs a Postgres database matching `backend/.env.example`:

```
DATABASE_URL=postgresql+asyncpg://syj:syj@localhost:5432/syj_launchpad
DATABASE_URL_SYNC=postgresql+psycopg2://syj:syj@localhost:5432/syj_launchpad
```

That is: **user `syj`, password `syj`, database `syj_launchpad`, port `5432`.**
Neither of these credentials pre-exist on a fresh Postgres install — they
have to be created once, by one of the two paths below. **This step is
required and is not optional setup** — skipping it is what produces
`asyncpg.exceptions.InvalidPasswordError: password authentication failed
for user "syj"`, which is a provisioning gap, not an application bug.

Postgres version: CI and `docker-compose.yml` both pin `postgres:17-alpine`.
Postgres 16 is also known to work (verified during development) — anything
16+ should behave identically for this schema, but 17 is the version this
project targets and tests against in CI.

## Path A — Docker (recommended, matches CI closest)

```bash
docker compose up -d
```

`docker-compose.yml` sets `POSTGRES_USER=syj`, `POSTGRES_PASSWORD=syj`,
`POSTGRES_DB=syj_launchpad` as container env vars — the role, password, and
database are created automatically on first container start. Nothing further
to do. If you previously started the container without these variables (or
changed them), remove the named volume and recreate it:

```bash
docker compose down -v
docker compose up -d
```

## Path B — Native/local Postgres install

If you're running Postgres directly (this is what a native Windows/macOS/Linux
Postgres service install gives you) rather than via Docker, the `syj` role
and `syj_launchpad` database do not exist yet on a stock install — you must
create them once, as a Postgres superuser:

**Linux/macOS:**
```bash
sudo -u postgres psql -c "CREATE USER syj WITH PASSWORD 'syj' SUPERUSER;"
sudo -u postgres psql -c "CREATE DATABASE syj_launchpad OWNER syj;"
```

**Windows** (PowerShell, using the `psql` that ships with the Postgres
installer — adjust the path/version to match your install, e.g.
`postgresql-x64-17`):
```powershell
& 'C:\Program Files\PostgreSQL\17\bin\psql.exe' -U postgres -c "CREATE USER syj WITH PASSWORD 'syj' SUPERUSER;"
& 'C:\Program Files\PostgreSQL\17\bin\psql.exe' -U postgres -c "CREATE DATABASE syj_launchpad OWNER syj;"
```
(You'll be prompted for the `postgres` superuser password you set during
installation.)

`SUPERUSER` here is a local-dev convenience so migrations/tests never trip
over missing grants — production deployments should use a least-privilege
role scoped to `syj_launchpad` only; see `docs/DEPLOYMENT.md`.

## Verifying setup worked

```bash
cd backend
cp .env.example .env   # set a real SECRET_KEY: openssl rand -hex 32
pip install -e ".[dev]"
alembic upgrade head
```

If `alembic upgrade head` completes without error and
`psql -U syj -d syj_launchpad -c '\dt'` (native) or
`docker compose exec postgres psql -U syj -d syj_launchpad -c '\dt'` (Docker)
lists `users`, `wallets`, and `siwe_nonces`, setup is correct. Then:

```bash
uvicorn app.main:app --reload
curl http://localhost:8000/api/v1/health   # expect "database": "connected"
```

## Running tests

The test suite (`pytest`, run from `backend/`) connects to the same
`DATABASE_URL`/`DATABASE_URL_SYNC` as the app — there is no separate mocked
test database. Point these at a real (Docker or native) Postgres instance
before running `pytest`; a database that isn't reachable will fail every
test with a connection error, not a test assertion failure — that's a setup
problem, not a code regression.
