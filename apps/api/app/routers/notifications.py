from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.errors import not_found
from app.models import Notification, User

router = APIRouter(prefix="/notifications", tags=["notifications"])


class ReadRequest(BaseModel):
    ids: list[int]


@router.get("")
def list_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.created_at.desc()).all()
    return [
        {"id": r.id, "type": r.type, "payload": r.payload, "created_at": r.created_at, "read_at": r.read_at}
        for r in rows
    ]


@router.post("/read")
def mark_read(body: ReadRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Notification).filter(Notification.user_id == user.id, Notification.id.in_(body.ids)).all()
    if not rows:
        raise not_found("Уведомления не найдены")
    now = datetime.now(timezone.utc)
    for r in rows:
        r.read_at = now
        db.add(r)
    db.commit()
    return {"updated": len(rows)}
