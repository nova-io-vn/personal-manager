from datetime import datetime, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.cloud import get_cloud_db
from app.models.cloud import CloudDevice, CloudUser, SyncChange
from app.schemas.cloud import AuthResponse, DeviceRead, DeviceRegisterRequest, LoginRequest, RegisterRequest, SyncChangeRead, SyncPullResponse, SyncPushRequest, SyncPushResponse, UserRead
from app.services.auth import create_access_token, decode_access_token, hash_password, new_id, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
sync_router = APIRouter(prefix="/sync", tags=["sync"])
bearer = HTTPBearer(auto_error=False)


def identity(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Thiếu access token")
    try:
        payload = decode_access_token(credentials.credentials)
    except (jwt.InvalidTokenError, RuntimeError):
        raise HTTPException(status_code=401, detail="Access token không hợp lệ hoặc đã hết hạn") from None
    if not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Access token thiếu user id")
    return payload


def user_device(db: Session, user_id: str, device_id: str) -> CloudDevice:
    device = db.scalar(select(CloudDevice).where(CloudDevice.id == device_id, CloudDevice.user_id == user_id))
    if device is None:
        raise HTTPException(status_code=403, detail="Thiết bị không thuộc tài khoản này")
    device.last_seen_at = datetime.now(timezone.utc)
    return device


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_cloud_db)):
    if not __import__("app.config", fromlist=["get_settings"]).get_settings().jwt_secret_key.strip():
        raise HTTPException(status_code=503, detail="JWT authentication chưa được cấu hình")
    if db.scalar(select(CloudUser).where(CloudUser.email == data.email)) is not None:
        raise HTTPException(status_code=409, detail="Email đã được đăng ký")
    user = CloudUser(id=new_id(), email=data.email, password_hash=hash_password(data.password))
    device = CloudDevice(id=new_id(), user_id=user.id, device_key=f"device-{new_id()}", name="Personal Manager", platform="desktop")
    db.add_all([user, device])
    db.commit()
    try:
        token = create_access_token(user.id, user.email, device.id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="JWT authentication chưa được cấu hình") from exc
    return AuthResponse(access_token=token, user=UserRead.model_validate(user), device_id=device.id)


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, db: Session = Depends(get_cloud_db)):
    if not __import__("app.config", fromlist=["get_settings"]).get_settings().jwt_secret_key.strip():
        raise HTTPException(status_code=503, detail="JWT authentication chưa được cấu hình")
    user = db.scalar(select(CloudUser).where(CloudUser.email == data.email))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
    device = db.scalar(select(CloudDevice).where(CloudDevice.user_id == user.id, CloudDevice.device_key == data.device_key))
    if device is None:
        device = CloudDevice(id=new_id(), user_id=user.id, device_key=data.device_key, name=data.device_name, platform=data.platform)
        db.add(device)
    else:
        device.name, device.platform = data.device_name, data.platform
        device.last_seen_at = datetime.now(timezone.utc)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    try:
        token = create_access_token(user.id, user.email, device.id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="JWT authentication chưa được cấu hình") from exc
    return AuthResponse(access_token=token, user=UserRead.model_validate(user), device_id=device.id)


@router.get("/me", response_model=UserRead)
def me(auth: dict = Depends(identity), db: Session = Depends(get_cloud_db)):
    user = db.get(CloudUser, auth["sub"])
    if user is None:
        raise HTTPException(status_code=401, detail="Tài khoản không tồn tại")
    return UserRead.model_validate(user)


@sync_router.post("/devices", response_model=DeviceRead)
def register_device(data: DeviceRegisterRequest, auth: dict = Depends(identity), db: Session = Depends(get_cloud_db)):
    device = db.scalar(select(CloudDevice).where(CloudDevice.user_id == auth["sub"], CloudDevice.device_key == data.device_key))
    if device is None:
        device = CloudDevice(id=new_id(), user_id=auth["sub"], device_key=data.device_key, name=data.name, platform=data.platform)
        db.add(device)
    else:
        device.name, device.platform = data.name, data.platform
        device.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    return DeviceRead.model_validate(device)


@sync_router.post("/push", response_model=SyncPushResponse)
def push(data: SyncPushRequest, auth: dict = Depends(identity), db: Session = Depends(get_cloud_db)):
    device = user_device(db, auth["sub"], data.device_id)
    accepted = duplicates = 0
    for item in data.changes:
        if db.scalar(select(SyncChange).where(SyncChange.user_id == auth["sub"], SyncChange.idempotency_key == item.idempotency_key)) is not None:
            duplicates += 1
            continue
        db.add(SyncChange(user_id=auth["sub"], device_id=device.id, entity_type=item.entity_type, entity_id=item.entity_id, operation=item.operation, payload=item.payload, idempotency_key=item.idempotency_key, occurred_at=item.occurred_at or datetime.now(timezone.utc)))
        accepted += 1
    db.commit()
    cursor = db.scalar(select(SyncChange.id).where(SyncChange.user_id == auth["sub"]).order_by(SyncChange.id.desc()).limit(1)) or 0
    return SyncPushResponse(accepted=accepted, duplicates=duplicates, cursor=cursor)


@sync_router.get("/pull", response_model=SyncPullResponse)
def pull(cursor: int = Query(default=0, ge=0), limit: int = Query(default=200, ge=1, le=500), auth: dict = Depends(identity), db: Session = Depends(get_cloud_db)):
    query = select(SyncChange).where(SyncChange.user_id == auth["sub"], SyncChange.id > cursor).order_by(SyncChange.id).limit(limit)
    if auth.get("device_id"):
        query = query.where(SyncChange.device_id != auth["device_id"])
    changes = db.scalars(query).all()
    next_cursor = changes[-1].id if changes else cursor
    return SyncPullResponse(changes=[SyncChangeRead(cursor=item.id, entity_type=item.entity_type, entity_id=item.entity_id, operation=item.operation, payload=item.payload, occurred_at=item.occurred_at, device_id=item.device_id) for item in changes], next_cursor=next_cursor)
