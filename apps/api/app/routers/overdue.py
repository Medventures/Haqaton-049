from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_role
from app.db import get_db
from app.models import Family, User
from app.modules.engine.catalog import get_catalog
from app.modules.plans.service import get_latest_plan
from app.modules.scheduler.escalation import recompute_family

router = APIRouter(tags=["overdue"])


@router.get("/overdue")
def list_overdue(db: Session = Depends(get_db), curator: User = Depends(require_role("curator"))):
    catalog = get_catalog()
    families = db.query(Family).filter(Family.curator_id == curator.id).all()
    result = []
    for family in families:
        recompute_family(db, family, catalog)
        plan = get_latest_plan(db, family.id)
        if plan is None:
            continue
        for step in plan.plan_json["steps"]:
            if step["status"] == "overdue":
                result.append(
                    {
                        "family_id": family.id,
                        "child_name": family.child_name,
                        "step_id": step["step_id"],
                        "service_id": step["service_id"],
                        "agency": step["agency"],
                        "deadline": step["deadline"],
                        "escalation_level": step["escalation_level"],
                    }
                )
    return result
