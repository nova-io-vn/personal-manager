"""Render entrypoint: migrate once, then start the FastAPI process."""

import os
from pathlib import Path

import uvicorn
from alembic import command
from alembic.config import Config


def migrate() -> None:
    database_url = os.getenv("ALEMBIC_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for Render deployment")
    root = Path(__file__).resolve().parent
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, "head")


def main() -> None:
    migrate()
    os.environ["PM_SKIP_STARTUP_MIGRATIONS"] = "1"
    # The migration uses the direct URL, while application traffic uses the
    # pooled cloud URL. This also prevents a stale local DATABASE_URL from
    # opening an empty SQLite database during FastAPI startup.
    os.environ["PM_USE_CLOUD_DATABASE"] = "1"
    uvicorn.run(
        "api.index:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "10000")),
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    main()
