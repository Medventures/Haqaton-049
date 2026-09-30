from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_role
from app.db import get_db
from app.models import Family, User
from app.modules.plans.service import get_latest_plan

router = APIRouter(prefix="/families", tags=["families"])


@router.get("")
def list_families(db: Session = Depends(get_db), curator: User = Depends(require_role("curator"))):
    families = db.query(Family).filter(Family.curator_id == curator.id).all()
    result = []
    for family in families:
        plan = get_latest_plan(db, family.id)
        result.append(
            {
                "id": family.id,
                "child_name": family.child_name,
                "region": family.region,
                "plan_status": plan.status if plan else None,
                "plan_version": plan.version if plan else None,
            }
        )
    return result
