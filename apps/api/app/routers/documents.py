from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import require_role
from app.db import get_db
from app.deps import get_family_for_curator, get_family_for_parent, get_own_family_for_parent
from app.errors import forbidden, not_found
from app.models import Document, User
from app.modules.documents.service import upload_document

router = APIRouter(prefix="/documents", tags=["documents"])


class PatchDocumentRequest(BaseModel):
    confirmed_by_parent: bool | None = None
    verified: bool | None = None


@router.post("")
async def create_document(
    file: UploadFile = File(...),
    doc_type_hint: str | None = Form(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("parent", "curator")),
):
    family = get_own_family_for_parent(db, user) if user.role == "parent" else None
    if family is None and user.role == "curator":
        raise forbidden("Куратор загружает документы через карточку семьи (этап 3, веб)")
    content = await file.read()
    doc = upload_document(db, family.id, file.filename, file.content_type or "application/octet-stream", content, doc_type_hint)
    return {
        "id": doc.id,
        "doc_type": doc.doc_type,
        "issued_at": doc.issued_at,
        "valid_until": doc.valid_until,
        "issuer": doc.issuer,
    }


@router.get("")
def list_documents(family: int, db: Session = Depends(get_db), user: User = Depends(require_role("parent", "curator"))):
    if user.role == "parent":
        get_family_for_parent(db, family, user)
    else:
        get_family_for_curator(db, family, user)
    rows = db.query(Document).filter(Document.family_id == family).all()
    return [
        {
            "id": r.id,
            "doc_type": r.doc_type,
            "issued_at": r.issued_at,
            "valid_until": r.valid_until,
            "issuer": r.issuer,
            "confirmed_by_parent": r.confirmed_by_parent,
            "verified_by": r.verified_by,
        }
        for r in rows
    ]


@router.patch("/{document_id}")
def patch_document(
    document_id: int,
    body: PatchDocumentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("parent", "curator")),
):
    doc = db.get(Document, document_id)
    if doc is None:
        raise not_found("Документ не найден")
    if user.role == "parent":
        get_family_for_parent(db, doc.family_id, user)
        if body.confirmed_by_parent is not None:
            doc.confirmed_by_parent = body.confirmed_by_parent
        if body.verified is not None:
            raise forbidden("Отметка «проверено» доступна только куратору")
    else:
        get_family_for_curator(db, doc.family_id, user)
        if body.verified is not None:
            doc.verified_by = user.id if body.verified else None
        if body.confirmed_by_parent is not None:
            doc.confirmed_by_parent = body.confirmed_by_parent
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return {"id": doc.id, "confirmed_by_parent": doc.confirmed_by_parent, "verified_by": doc.verified_by}
