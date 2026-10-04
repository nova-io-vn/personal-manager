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
