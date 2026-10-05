from functools import lru_cache
import os
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Personal Manager API"
    database_url: str = ""
    personal_manager_data_dir: Path | None = None
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cloud_database_url: str = ""
    jwt_secret_key: str = ""
    jwt_access_token_minutes: int = 60 * 24 * 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def resolve_storage(self):
        if os.getenv("PM_PRODUCTION") == "1":
            if not self.database_url.strip():
                raise ValueError("DATABASE_URL is required in production")
            if not self.database_url.startswith(("postgresql://", "postgresql+psycopg://")):
                raise ValueError("Production DATABASE_URL must be a PostgreSQL URL")
        # Vercel functions have an ephemeral writable /tmp directory. A relative
        # SQLite path points into the read-only deployment bundle there.
        if os.getenv("VERCEL") == "1" and self.personal_manager_data_dir is None and self.database_url.startswith("sqlite"):
            self.database_url = "sqlite:////tmp/personal-manager.db"
        if self.personal_manager_data_dir is not None:
            data_dir = self.personal_manager_data_dir.expanduser().resolve()
            self.personal_manager_data_dir = data_dir
            self.database_url = f"sqlite:///{(data_dir / 'personal.db').as_posix()}"
        elif not self.database_url:
            self.database_url = "sqlite:///./data/personal.db"
        return self

    @property
    def data_dir(self) -> Path:
        if self.personal_manager_data_dir is not None:
            return self.personal_manager_data_dir
        if self.database_url.startswith("sqlite:///"):
            database_path = Path(self.database_url.removeprefix("sqlite:///"))
            return database_path.parent.resolve()
        return Path("data").resolve()

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
