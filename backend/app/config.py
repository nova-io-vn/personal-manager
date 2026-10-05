from functools import lru_cache
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
