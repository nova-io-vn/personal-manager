from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=200)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Email không hợp lệ")
        return normalized


class LoginRequest(RegisterRequest):
    device_key: str = Field(min_length=3, max_length=120)
    device_name: str = Field(default="Personal Manager", min_length=1, max_length=120)
    platform: str = Field(default="desktop", min_length=1, max_length=30)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserRead
    device_id: str


class DeviceRegisterRequest(BaseModel):
    device_key: str = Field(min_length=3, max_length=120)
    name: str = Field(default="Personal Manager", min_length=1, max_length=120)
    platform: str = Field(default="desktop", min_length=1, max_length=30)


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    device_key: str
    name: str
    platform: str
    last_seen_at: datetime


class SyncChangeInput(BaseModel):
    entity_type: str = Field(min_length=1, max_length=80)
    entity_id: str = Field(min_length=1, max_length=120)
    operation: Literal["UPSERT", "DELETE"]
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=8, max_length=180)
    occurred_at: datetime | None = None


class SyncPushRequest(BaseModel):
    device_id: str
    changes: list[SyncChangeInput] = Field(default_factory=list, max_length=500)


class SyncPushResponse(BaseModel):
    accepted: int
    duplicates: int
    cursor: int


class SyncChangeRead(BaseModel):
    cursor: int
    entity_type: str
    entity_id: str
    operation: str
    payload: dict[str, Any]
    occurred_at: datetime
    device_id: str


class SyncPullResponse(BaseModel):
    changes: list[SyncChangeRead]
    next_cursor: int
