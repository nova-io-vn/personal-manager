from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect

from app.database.base import Base


ALEMBIC_REVISION = "0001_initial"


class IncompatibleDatabaseError(RuntimeError):
    pass


def _config(database_url: str) -> Config:
    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def verify_legacy_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    expected = set(Base.metadata.tables)
    missing_tables = expected - existing
    if missing_tables:
        raise IncompatibleDatabaseError(
            "Existing database is missing required tables: " + ", ".join(sorted(missing_tables))
        )
    for table_name, table in Base.metadata.tables.items():
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        missing_columns = {column.name for column in table.columns} - columns
        if missing_columns:
            raise IncompatibleDatabaseError(
                f"Existing table {table_name} is missing columns: {', '.join(sorted(missing_columns))}"
            )


def ensure_database_schema(engine: Engine, database_url: str) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    config = _config(database_url)
    if "alembic_version" in tables:
        command.upgrade(config, "head")
        return
    application_tables = tables.intersection(Base.metadata.tables)
    if application_tables:
        verify_legacy_schema(engine)
        command.stamp(config, ALEMBIC_REVISION)
        return
    command.upgrade(config, "head")
