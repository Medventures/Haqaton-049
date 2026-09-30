from fastapi import APIRouter, Depends

from app.auth import require_role
from app.modules.engine.catalog import get_catalog

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/services")
def list_services(curator=Depends(require_role("curator"))):
    return get_catalog().services_list
