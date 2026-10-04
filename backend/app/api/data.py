from datetime import datetime, timezone

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.config import get_settings
from app.database.database import engine
from app.schemas.data import BackupInfo, RestoreResult
from app.services.backup import BackupService, BackupValidationError, MAX_BACKUP_BYTES

router = APIRouter(prefix="/data", tags=["data"])


def _service() -> BackupService:
    return BackupService(engine, get_settings().data_dir)


@router.get("/backups/latest", response_model=BackupInfo | None)
def latest_backup():
    path = _service().latest_backup()
    if path is None:
        return None
    stat = path.stat()
    return BackupInfo(
        filename=path.name,
        created_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc),
        size_bytes=stat.st_size,
    )


@router.post("/backup", response_class=FileResponse)
def create_backup():
    path = _service().create_backup()
    return FileResponse(path, media_type="application/zip", filename=path.name)


@router.post("/restore", response_model=RestoreResult)
async def restore_backup(file: UploadFile = File(...)):
    content = await file.read(MAX_BACKUP_BYTES + 1)
    try:
        safety_backup = _service().restore(content)
    except BackupValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return RestoreResult(
        success=True,
        safety_backup=safety_backup.name,
        restart_required=True,
        message="Dữ liệu đã được khôi phục. Một bản sao an toàn đã được tạo trước khi thay thế.",
    )
