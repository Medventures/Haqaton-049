from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_role
from app.db import get_db
from app.deps import get_own_family_for_parent
from app.models import Family, User
from app.modules.plans.service import get_latest_plan

router = APIRouter(prefix="/families", tags=["families"])


@router.get("/me")
def my_family(db: Session = Depends(get_db), parent: User = Depends(require_role("parent"))):
    family = get_own_family_for_parent(db, parent)
    return {"id": family.id, "child_name": family.child_name}


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
