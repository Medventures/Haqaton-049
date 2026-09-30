"""Кошелёк документов и распознавание (раздел 8 SPEC.md).

Извлечение текста — best-effort через `pdfplumber` для цифровых PDF.
Сканы/фото (`pytesseract`) не реализованы в этом окружении: нет системного
бинаря tesseract, см. docs/OPEN_QUESTIONS.md. Разбор реквизитов — через
LLM-модуль (вызов 4), в режиме заглушки возвращает пустые поля, поэтому
тесты этого модуля мокают `llm_client.parse_document`.
"""
import copy
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.errors import bad_request
from app.models import Document, Interview
from app.modules.llm import client as llm_client
from app.paths import REPO_ROOT

UPLOAD_DIR = REPO_ROOT / "apps" / "api" / "uploads"

# Раздел 8: какие doc_type при загрузке обновляют профиль.
PROFILE_UPDATE_FIELDS = {
    "pmpk_conclusion": "pmpk.valid_until",
    "disability_conclusion": "disability.review_date",
}


def _extract_text(file_bytes: bytes, content_type: str) -> str:
    if content_type == "application/pdf":
        try:
            import io

            import pdfplumber

            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception:
            return ""
    if content_type.startswith("text/"):
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return ""
    return ""


def _update_profile(db: Session, family_id: int, doc_type: str, value: str | None):
    if not value:
        return
    field_path = PROFILE_UPDATE_FIELDS.get(doc_type)
    if not field_path:
        return
    interview = (
        db.query(Interview)
        .filter(Interview.family_id == family_id)
        .order_by(Interview.id.desc())
        .first()
    )
    if interview is None:
        return
    profile = copy.deepcopy(interview.profile or {})
    node = profile
    parts = field_path.split(".")
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value
    interview.profile = profile
    db.add(interview)
    db.commit()


def upload_document(
    db: Session,
    family_id: int,
    filename: str,
    content_type: str,
    file_bytes: bytes,
    doc_type_hint: str | None = None,
) -> Document:
    if not file_bytes:
        raise bad_request("Пустой файл")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"{family_id}-{int(datetime.now(timezone.utc).timestamp() * 1000)}-{Path(filename).name}"
    file_path = UPLOAD_DIR / safe_name
    file_path.write_bytes(file_bytes)

    text = _extract_text(file_bytes, content_type)
    parsed = llm_client.parse_document(text, db=db) if text else {"doc_type": None, "issued_at": None, "valid_until": None, "issuer": None}

    doc_type = parsed.get("doc_type") or doc_type_hint
    if not doc_type:
        raise bad_request("Не удалось определить тип документа, укажите doc_type_hint")

    row = Document(
        family_id=family_id,
        doc_type=doc_type,
        file_path=str(file_path.relative_to(REPO_ROOT)),
        issued_at=parsed.get("issued_at"),
        valid_until=parsed.get("valid_until"),
        issuer=parsed.get("issuer"),
        confirmed_by_parent=False,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    _update_profile(db, family_id, doc_type, parsed.get("valid_until"))
    return row
