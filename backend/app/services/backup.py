import json
import sqlite3
import tempfile
import zipfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from sqlalchemy import Engine, create_engine

from app.database.migrations import ALEMBIC_REVISION, IncompatibleDatabaseError, verify_legacy_schema


APP_VERSION = "0.1.0"
MAX_BACKUP_BYTES = 512 * 1024 * 1024


class BackupValidationError(ValueError):
    pass


class BackupService:
    def __init__(self, engine: Engine, data_dir: Path):
        self.engine = engine
        self.data_dir = data_dir.resolve()
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, prefix: str = "personal-manager-backup") -> Path:
        timestamp = datetime.now(timezone.utc)
        stamp = timestamp.strftime("%Y-%m-%d-%H%M%S")
        archive = self.backup_dir / f"{prefix}-{stamp}.zip"
        with tempfile.TemporaryDirectory(dir=self.data_dir) as temp_dir:
            database_copy = Path(temp_dir) / "personal.db"
            self._backup_database(database_copy)
            self._check_integrity(database_copy)
            manifest = {
                "application": "Personal Manager",
                "application_version": APP_VERSION,
                "schema_revision": self._schema_revision(database_copy),
                "created_at": timestamp.isoformat(),
            }
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                bundle.write(database_copy, "personal.db")
                bundle.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        return archive

    def latest_backup(self) -> Path | None:
        backups = sorted(self.backup_dir.glob("*.zip"), key=lambda item: item.stat().st_mtime, reverse=True)
        return backups[0] if backups else None

    def restore(self, archive_bytes: bytes) -> Path:
        if not archive_bytes or len(archive_bytes) > MAX_BACKUP_BYTES:
            raise BackupValidationError("Backup is empty or exceeds the 512 MB limit.")
        with tempfile.TemporaryDirectory(dir=self.data_dir) as temp_dir:
            archive_path = Path(temp_dir) / "restore.zip"
            archive_path.write_bytes(archive_bytes)
            database_path = self._validate_and_extract(archive_path, Path(temp_dir))
            safety_backup = self.create_backup(prefix="pre-restore-safety")
            self._restore_database(database_path)
            self.engine.dispose()
            return safety_backup

    def _backup_database(self, destination: Path) -> None:
        raw = self.engine.raw_connection()
        try:
            source = raw.driver_connection
            target = sqlite3.connect(destination)
            try:
                source.backup(target)
            finally:
                target.close()
        finally:
            raw.close()

    def _restore_database(self, source_path: Path) -> None:
        source = sqlite3.connect(source_path)
        raw = self.engine.raw_connection()
        try:
            destination = raw.driver_connection
            source.backup(destination)
            destination.commit()
        finally:
            raw.close()
            source.close()

    def _validate_and_extract(self, archive_path: Path, temp_dir: Path) -> Path:
        try:
            with zipfile.ZipFile(archive_path) as bundle:
                names = {item.filename for item in bundle.infolist()}
                if names != {"personal.db", "manifest.json"}:
                    raise BackupValidationError("Backup archive has an invalid structure.")
                if any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names):
                    raise BackupValidationError("Backup archive contains an unsafe path.")
                if sum(item.file_size for item in bundle.infolist()) > MAX_BACKUP_BYTES:
                    raise BackupValidationError("Backup contents exceed the 512 MB limit.")
                manifest = json.loads(bundle.read("manifest.json"))
                if manifest.get("application") != "Personal Manager":
                    raise BackupValidationError("This is not a Personal Manager backup.")
                if manifest.get("schema_revision") != ALEMBIC_REVISION:
                    raise BackupValidationError("Backup schema is not compatible with this application version.")
                database_path = temp_dir / "validated-personal.db"
                database_path.write_bytes(bundle.read("personal.db"))
        except (zipfile.BadZipFile, json.JSONDecodeError, KeyError) as exc:
            raise BackupValidationError("Backup archive is invalid or corrupt.") from exc
        self._check_integrity(database_path)
        candidate_engine = create_engine(f"sqlite:///{database_path.as_posix()}")
        try:
            verify_legacy_schema(candidate_engine)
            if self._schema_revision(database_path) != ALEMBIC_REVISION:
                raise BackupValidationError("Backup database schema version is not supported.")
        except IncompatibleDatabaseError as exc:
            raise BackupValidationError(str(exc)) from exc
        finally:
            candidate_engine.dispose()
        return database_path

    @staticmethod
    def _check_integrity(database_path: Path) -> None:
        try:
            with closing(sqlite3.connect(database_path)) as connection:
                result = connection.execute("PRAGMA integrity_check").fetchone()
        except sqlite3.DatabaseError as exc:
            raise BackupValidationError("Backup database is not a valid SQLite database.") from exc
        if result is None or result[0] != "ok":
            raise BackupValidationError("Backup database failed its integrity check.")

    @staticmethod
    def _schema_revision(database_path: Path) -> str | None:
        try:
            with closing(sqlite3.connect(database_path)) as connection:
                exists = connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='alembic_version'"
                ).fetchone()
                if exists is None:
                    return None
                row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
                return row[0] if row else None
        except sqlite3.DatabaseError:
            return None
