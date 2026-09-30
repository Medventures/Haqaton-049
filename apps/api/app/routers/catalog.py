from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import clock
from app.auth import get_current_user, require_role
from app.db import get_db
from app.modules.engine.catalog import get_catalog

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/services")
def list_services(curator=Depends(require_role("curator"))):
    return get_catalog().services_list


@router.get("/reference")
def reference(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Справочники для подсказок на экране шага (раздел 15.1) и текущая дата
    приложения с учётом демо-сдвига (раздел 19.3) для календаря."""
    catalog = get_catalog()
    doc_fields = ("doc_type", "title_ru", "title_kk", "issuer_ru", "issuer_kk", "validity_ru", "validity_kk")
    provider_fields = (
        "provider_id", "name_ru", "name_kk", "address_ru", "address_kk", "phone", "hours_ru", "hours_kk", "booking_methods",
    )
    return {
        "today": clock.today(db).isoformat(),
        "document_types": {k: {f: d.get(f) for f in doc_fields} for k, d in catalog.document_types.items()},
        "providers": {k: {f: p.get(f) for f in provider_fields} for k, p in catalog.providers.items()},
    }
