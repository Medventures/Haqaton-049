from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import require_role
from app.config import get_settings
from app.db import get_db
from app.errors import forbidden
from app.models import Escalation, Family, Outbox, Setting, User
from app.modules.scheduler.escalation import revert_time_shift
from app import clock

router = APIRouter(tags=["demo"])


def _require_demo_mode():
    if not get_settings().demo_mode:
        raise forbidden("Доступно только в DEMO_MODE")


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
