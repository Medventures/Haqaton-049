"""Уведомления (раздел 18 SPEC.md): центр + email. Всё, что уходит на
email, дублируется в центр. При MAIL_MODE=console письмо не отправляется,
а пишется в outbox."""
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Notification, Outbox, User

# Раздел 18: события и каналы по умолчанию (email можно отключить
# родителем для напоминаний/истекающих документов — раздел 18, последний
# абзац; сама модель отключения — стадия 3/веб, здесь только каналы).
EMAIL_OPTIONAL_TYPES = {"escalation_0", "document_expiring_30d"}


def notify(db: Session, user: User | None, notif_type: str, payload: dict, channels: list[str] | None = None):
    if user is None:
        return None
    channels = channels or ["center"]
    row = Notification(user_id=user.id, type=notif_type, payload=payload, channels=channels)
    db.add(row)
    if "email" in channels:
        settings = get_settings()
        subject, body = _render_email(notif_type, payload, user.lang)
        if settings.mail_mode == "console":
            db.add(Outbox(to_email=user.email, subject=subject, body=body))
    db.commit()
    db.refresh(row)
    return row


_SUBJECTS = {
    "draft_ready": {"ru": "План готов к проверке", "kk": "Жоспар тексеруге дайын"},
    "plan_approved": {"ru": "План подтверждён", "kk": "Жоспар бекітілді"},
    "red_flag": {"ru": "Внимание: отмечен красный флаг", "kk": "Назар аударыңыз: белгі қойылды"},
    "clarify_requested": {"ru": "Куратор просит уточнение", "kk": "Куратор нақтылау сұрайды"},
    "escalation_0": {"ru": "Срок приближается", "kk": "Мерзім жақындап келеді"},
    "escalation_1": {"ru": "Шаг просрочен", "kk": "Қадам мерзімі өтті"},
    "escalation_2": {"ru": "Требует действия", "kk": "Әрекетті қажет етеді"},
    "escalation_3": {"ru": "Эскалировано в ведомство", "kk": "Ведомствоға көтерілді"},
    "document_expiring_30d": {"ru": "Документ скоро истекает", "kk": "Құжаттың мерзімі жақында аяқталады"},
}


def _render_email(notif_type: str, payload: dict, lang: str) -> tuple[str, str]:
    lang = lang if lang in ("ru", "kk") else "ru"
    subject = _SUBJECTS.get(notif_type, {}).get(lang, notif_type)
    body = "\n".join(f"{k}: {v}" for k, v in payload.items())
    return subject, body
