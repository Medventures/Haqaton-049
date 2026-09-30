"""Фильтр формулировок (раздел 12.3 SPEC.md)."""
import json
import re

from app.paths import DATA_DIR

_PATTERNS = None


def _load():
    global _PATTERNS
    if _PATTERNS is None:
        with open(DATA_DIR / "filter_patterns.json", encoding="utf-8") as f:
            _PATTERNS = json.load(f)
    return _PATTERNS


def check_text(text: str, lang: str = "ru") -> list[dict]:
    """Возвращает список сработавших правил: [{category, pattern}]."""
    data = _load()
    cleaned = text
    for phrase in data["allowlist"]:
        cleaned = re.sub(re.escape(phrase), "", cleaned, flags=re.IGNORECASE)

    hits = []
    for category, patterns_by_lang in data["categories"].items():
        for pattern in patterns_by_lang.get(lang, []):
            if re.search(pattern, cleaned, flags=re.IGNORECASE):
                hits.append({"category": category, "pattern": pattern})
    return hits
