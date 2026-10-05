import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

from app.config import get_settings


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 240_000)
    return f"pbkdf2_sha256$240000${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds))
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: str, email: str, device_id: str | None = None) -> str:
    secret = get_settings().jwt_secret_key.strip()
    if not secret:
        raise RuntimeError("JWT authentication is not configured. Set JWT_SECRET_KEY.")
    now = datetime.now(timezone.utc)
    payload = {"sub": user_id, "email": email, "device_id": device_id, "iat": now, "exp": now + timedelta(minutes=get_settings().jwt_access_token_minutes)}
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    secret = get_settings().jwt_secret_key.strip()
    if not secret:
        raise RuntimeError("JWT authentication is not configured. Set JWT_SECRET_KEY.")
    return jwt.decode(token, secret, algorithms=["HS256"])


def new_id() -> str:
    return str(uuid4())
