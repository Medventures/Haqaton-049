import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.auth import (
    COOKIE_NAME,
    create_session_token,
    get_current_user,
    hash_password,
    require_role,
    verify_password,
)
from app.config import get_settings
from app.db import get_db
from app.errors import bad_request, conflict, not_found
from app.models import Family, Invite, Outbox, User

router = APIRouter(prefix="/auth", tags=["auth"])

INVITE_TTL_DAYS = 14


class InviteRequest(BaseModel):
    email: EmailStr
    child_name: str
    child_birth_date: str | None = None
    region: str | None = None


class RegisterRequest(BaseModel):
    token: str
    name: str
    password: str
    consent: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def _set_session_cookie(response: Response, token: str):
    settings = get_settings()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.api_url.startswith("https"),
        max_age=settings.jwt_ttl_hours * 3600,
    )


@router.post("/invite")
def invite(body: InviteRequest, response: Response, db: Session = Depends(get_db), curator: User = Depends(require_role("curator"))):
    family = Family(
        child_name=body.child_name,
        child_birth_date=body.child_birth_date,
        region=body.region,
        curator_id=curator.id,
        parent_id=None,
    )
    db.add(family)
    db.commit()
    db.refresh(family)

    token = secrets.token_urlsafe(32)
    invite_row = Invite(
        token=token,
        family_id=family.id,
        email=body.email,
        expires_at=datetime.now(timezone.utc) + timedelta(days=INVITE_TTL_DAYS),
    )
    db.add(invite_row)

    settings = get_settings()
    if settings.mail_mode == "console":
        db.add(
            Outbox(
                to_email=body.email,
                subject="Приглашение в AqylRoute",
                body=f"Регистрация: {settings.api_url}/ru/invite/{token}",
            )
        )
    db.commit()
    return {"family_id": family.id, "token": token}


@router.post("/register")
def register(body: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    invite_row = db.get(Invite, body.token)
    if invite_row is None or invite_row.used_at is not None:
        raise bad_request("Приглашение недействительно")
    if invite_row.expires_at < datetime.now(timezone.utc):
        raise bad_request("Срок приглашения истёк")
    if not body.consent:
        raise bad_request("Нужно согласие на обработку данных")

    user = User(
        role="parent",
        name=body.name,
        email=invite_row.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.flush()

    family = db.get(Family, invite_row.family_id)
    family.parent_id = user.id
    invite_row.used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    token = create_session_token(user)
    _set_session_cookie(response, token)
    return {"id": user.id, "role": user.role, "name": user.name}


@router.post("/login")
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise bad_request("Неверный email или пароль")
    token = create_session_token(user)
    _set_session_cookie(response, token)
    return {"id": user.id, "role": user.role, "name": user.name}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "role": user.role, "name": user.name, "email": user.email, "lang": user.lang}
