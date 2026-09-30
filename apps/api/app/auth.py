"""Авторизация и роли (раздел 13 SPEC.md: JWT в httpOnly cookie)."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Cookie, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import User

COOKIE_NAME = "aqylroute_session"
_PBKDF2_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), _PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algo, iterations, salt, digest_hex = password_hash.split("$")
        if algo != "pbkdf2_sha256":
            return False
        computed = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations)
        )
        return hmac.compare_digest(computed.hex(), digest_hex)
    except (ValueError, AttributeError):
        return False


def create_session_token(user: User) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(hours=settings.jwt_ttl_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_session_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "invalid_session", "message": "Сессия недействительна"}},
        ) from exc


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    session_cookie: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> User:
    token = session_cookie
    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "unauthenticated", "message": "Нужна авторизация"}},
        )
    payload = decode_session_token(token)
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "unauthenticated", "message": "Пользователь не найден"}},
        )
    return user


def require_role(*roles: str):
    def _dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail={"error": {"code": "forbidden", "message": "Недостаточно прав"}},
            )
        return user

    return _dependency
