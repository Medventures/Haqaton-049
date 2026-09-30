from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import create_session_token, require_role
from app.config import get_settings
from app.db import get_db
from app.errors import forbidden, not_found
from app.models import Escalation, Family, Outbox, Setting, User
from app.modules.scheduler.escalation import revert_time_shift
from app import clock
from app.routers.auth import _set_session_cookie

router = APIRouter(tags=["demo"])


def _require_demo_mode():
    if not get_settings().demo_mode:
        raise forbidden("Доступно только в DEMO_MODE")


# Раздел 19.5: демо-аккаунты из сида. Быстрый вход без пароля только для них
# и только при DEMO_MODE.
DEMO_ACCOUNTS = [
    {"key": "parent_a", "email": "parent.a@demo.kz"},
    {"key": "parent_b", "email": "parent.b@demo.kz"},
    {"key": "curator", "email": "curator@demo.kz"},
]


class DemoLoginRequest(BaseModel):
    key: str


@router.get("/demo/accounts")
def demo_accounts(db: Session = Depends(get_db)):
    _require_demo_mode()
    result = []
    for account in DEMO_ACCOUNTS:
        user = db.query(User).filter(User.email == account["email"]).one_or_none()
        if user is not None:
            result.append({"key": account["key"], "role": user.role, "name": user.name, "email": user.email})
    return result


@router.post("/demo/login")
def demo_login(body: DemoLoginRequest, response: Response, db: Session = Depends(get_db)):
    _require_demo_mode()
    account = next((a for a in DEMO_ACCOUNTS if a["key"] == body.key), None)
    user = db.query(User).filter(User.email == account["email"]).one_or_none() if account else None
    if user is None:
        raise not_found("Демо-аккаунт не найден")
    _set_session_cookie(response, create_session_token(user))
    return {"id": user.id, "role": user.role, "name": user.name}


class TimeShiftRequest(BaseModel):
    offset_days: int


@router.get("/demo/state")
def state(db: Session = Depends(get_db), curator: User = Depends(require_role("curator"))):
    """Для демо-панели (раздел 15.2): текущая дата приложения и сдвиг."""
    _require_demo_mode()
    return {"time_offset_days": clock.get_time_offset_days(db), "today": clock.today(db).isoformat()}


@router.post("/demo/time-shift")
def time_shift(body: TimeShiftRequest, db: Session = Depends(get_db), curator: User = Depends(require_role("curator"))):
    _require_demo_mode()
    row = db.get(Setting, "time_offset_days")
    if row is None:
        row = Setting(key="time_offset_days", value=str(body.offset_days))
        db.add(row)
    else:
        row.value = str(body.offset_days)
    db.commit()
    return {"time_offset_days": body.offset_days, "today": clock.today(db).isoformat()}


@router.post("/demo/reset")
def reset(db: Session = Depends(get_db), curator: User = Depends(require_role("curator"))):
    _require_demo_mode()
    row = db.get(Setting, "time_offset_days")
    if row is None:
        db.add(Setting(key="time_offset_days", value="0"))
    else:
        row.value = "0"
    db.query(Escalation).delete()
    db.commit()
    for family in db.query(Family).all():
        revert_time_shift(db, family)
    return {"ok": True}


@router.get("/dev/mail")
def dev_mail(db: Session = Depends(get_db)):
    _require_demo_mode()
    rows = db.query(Outbox).order_by(Outbox.id.desc()).all()
    return [{"id": r.id, "to_email": r.to_email, "subject": r.subject, "body": r.body, "created_at": r.created_at} for r in rows]
