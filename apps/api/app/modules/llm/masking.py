"""Маскирование перед вызовом LLM (раздел 12.1 SPEC.md).

Имя ребёнка, ФИО родителей, 12-значные числа (ИИН), телефоны, email и
точные адреса заменяются метками [CHILD], [PARENT], [ID], [PHONE],
[EMAIL], [ADDRESS]. Обратная подстановка не нужна.
"""
import re

_IIN_RE = re.compile(r"\b\d{12}\b")
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE_RE = re.compile(r"(?:\+?7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b")
# Эвристика: улица/микрорайон/дом/квартира + номер. Точная гео-разметка
# адресов вне стека проекта, поэтому детект best-effort (см. docs/DECISIONS.md).
_ADDRESS_RE = re.compile(
    r"\b(?:мкр\.?|ул\.?|улица|пр\.?|проспект|дом|д\.)\s*[\wа-яА-ЯёЁ\-]*\s*,?\s*\d+[а-яА-Я]?"
    r"(?:\s*,?\s*(?:кв\.?|квартира|подъезд)\s*\d+)?",
    re.IGNORECASE,
)


def _mask_name(text: str, name: str | None, tag: str) -> str:
    if not name:
        return text
    parts = [p for p in re.split(r"\s+", name.strip()) if len(p) > 1]
    for part in parts:
        text = re.sub(rf"\b{re.escape(part)}\b", tag, text, flags=re.IGNORECASE)
    return text


def mask_text(text: str, child_name: str | None = None, parent_name: str | None = None) -> str:
    if not text:
        return text
    masked = text
    masked = _mask_name(masked, child_name, "[CHILD]")
    masked = _mask_name(masked, parent_name, "[PARENT]")
    masked = _EMAIL_RE.sub("[EMAIL]", masked)
    masked = _PHONE_RE.sub("[PHONE]", masked)
    masked = _IIN_RE.sub("[ID]", masked)
    masked = _ADDRESS_RE.sub("[ADDRESS]", masked)
    return masked
