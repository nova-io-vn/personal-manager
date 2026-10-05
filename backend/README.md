# Personal Manager backend

FastAPI + SQLAlchemy + SQLite API for the local-first Personal Manager application.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is at http://127.0.0.1:8000; Swagger is at http://127.0.0.1:8000/docs. In Git Bash, activate with `source .venv/Scripts/activate`.

Run tests with `python -m pytest`. Pytest uses temporary SQLite databases; it does not open `data/personal.db`.

## Database

Development defaults to `data/personal.db` (or `DATABASE_URL`). Desktop startup sets `PERSONAL_MANAGER_DATA_DIR` to Electron's writable `userData` directory; the backend uses `<data-dir>/personal.db` and stores backups/logs beside it.

Alembic migrations run at application startup. A new database upgrades from zero. A legacy database is stamped at the initial revision only after checking that all current tables and columns exist; it is never dropped. If schema compatibility fails, startup stops with the data left intact. See the repository root README for desktop packaging and backup/restore details.

## Integrations and time

Finance, Calendar, Health, Nutrition, Journal, Settings, and Notifications are local. Gemini and Telegram are optional. Their credentials are stored locally in SQLite without encryption; API responses mask the keys. LOCAL notifications are in-app records, not native Windows toasts. Configured reminder times use local time; calendar timestamps use the frontend's ISO representation.

## Cloud authentication and sync

The Desktop application and Android APK use the same FastAPI service and PostgreSQL database. Authentication is not required for this single-owner deployment. `CLOUD_DATABASE_URL` and `JWT_SECRET_KEY` are not needed by the normal application flow.

Available endpoints are `/api/auth/register`, `/api/auth/login`, `/api/auth/me`, `/api/sync/devices`, `/api/sync/push`, and `/api/sync/pull`. The current sync API stores authenticated changes with idempotency protection; a client adapter must apply pulled changes to its local store.

### Render + PostgreSQL

For the Render Web Service use `backend` as the root directory:

```text
Build Command: pip install -r requirements.txt
Start Command: python render_start.py
```

Set these variables in Render:

```text
DATABASE_URL=<Neon pooled PostgreSQL URL>
ALEMBIC_DATABASE_URL=<Neon direct/unpooled PostgreSQL URL>
CORS_ORIGINS=https://your-frontend-domain,capacitor://localhost,http://localhost
```

`render_start.py` migrates PostgreSQL once using the direct URL, then starts
FastAPI with `DATABASE_URL`. If `DATABASE_URL` is temporarily missing, the
application falls back to `ALEMBIC_DATABASE_URL`; defining the pooled URL is
still preferred. Production rejects SQLite URLs, so a misconfigured
deployment cannot silently create an empty local database. Do not use the
pooled URL for Alembic migrations.
