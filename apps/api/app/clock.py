"""Сервис часов (раздел 11.3 SPEC.md).

Единственный источник "сегодня" во всём приложении. Прямые вызовы
`date.today()` запрещены (раздел 21). Часовой пояс `Asia/Almaty`
(раздел 11.2: "Все даты календарные, часовой пояс Asia/Almaty").
"""
from datetime import date, datetime, timedelta

try:
    from zoneinfo import ZoneInfo

    _ALMATY = ZoneInfo("Asia/Almaty")
except Exception:  # pragma: no cover - tzdata missing on minimal systems
    _ALMATY = None


def _real_today() -> date:
    if _ALMATY is not None:
        return datetime.now(_ALMATY).date()
    return datetime.utcnow().date()


def get_time_offset_days(db) -> int:
    from app.models import Setting

    row = db.get(Setting, "time_offset_days")
    if row is None or row.value is None:
        return 0
    try:
        return int(row.value)
    except (TypeError, ValueError):
        return 0


def today(db=None) -> date:
    """Текущая дата с учётом `settings.time_offset_days` (демо-сдвиг)."""
    offset_days = get_time_offset_days(db) if db is not None else 0
    return _real_today() + timedelta(days=offset_days)
