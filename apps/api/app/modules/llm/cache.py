"""Кеш ответов LLM (раздел 12 SPEC.md): SHA-256 от типа вызова и входа."""
import hashlib
import json

from sqlalchemy.orm import Session

from app.models import LlmCache


def _key(call_type: str, payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(f"{call_type}:{canonical}".encode("utf-8")).hexdigest()


def get_cached(db: Session, call_type: str, payload: dict) -> dict | None:
    row = db.get(LlmCache, _key(call_type, payload))
    return row.response if row else None


def store(db: Session, call_type: str, payload: dict, response: dict) -> None:
    key = _key(call_type, payload)
    if db.get(LlmCache, key) is not None:
        return
    db.add(LlmCache(key=key, call_type=call_type, response=response))
    db.commit()
