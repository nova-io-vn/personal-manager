from datetime import datetime

from pydantic import BaseModel


class BackupInfo(BaseModel):
    filename: str
    created_at: datetime
    size_bytes: int


class RestoreResult(BaseModel):
    success: bool
    safety_backup: str
    restart_required: bool = True
    message: str
