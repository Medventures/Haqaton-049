from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_role
from app.db import get_db
from app.deps import get_family_for_curator, get_family_for_parent, get_own_family_for_parent
from app.errors import not_found
from app.models import CasePlan, User
from app.modules.engine.catalog import get_catalog
from app.modules.plans import service as plans_service

router = APIRouter(prefix="/plans", tags=["plans"])

_catalog = get_catalog()
_ServiceId = Literal[tuple(_catalog.services.keys())] if _catalog.services else str


class AddStepRequest(BaseModel):
    service_id: _ServiceId


class PatchStepRequest(BaseModel):
    status: str
    reason: str | None = None
    comment: str | None = None


@router.get("/{family_id}")
def get_plan(family_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("parent", "curator"))):
    if user.role == "parent":
        family = get_family_for_parent(db, family_id, user)
        plan = plans_service.get_plan_for_parent(db, family, user.id)
    else:
        family = get_family_for_curator(db, family_id, user)
        plan = plans_service.get_plan_for_curator(db, family, user.id)
    return plan.plan_json


@router.get("/{family_id}/versions")
def get_versions(family_id: int, db: Session = Depends(get_db), curator: User = Depends(require_role("curator"))):
    family = get_family_for_curator(db, family_id, curator)
    stmt = select(CasePlan).where(CasePlan.family_id == family.id).order_by(CasePlan.version.asc())
    rows = db.execute(stmt).scalars().all()
    return [{"version": r.version, "status": r.status, "created_by": r.created_by, "created_at": r.created_at} for r in rows]


@router.post("/{family_id}/approve")
def approve(family_id: int, db: Session = Depends(get_db), curator: User = Depends(require_role("curator"))):
    family = get_family_for_curator(db, family_id, curator)
    plan = plans_service.approve_plan(db, family, curator.id)
    return plan.plan_json


@router.post("/{family_id}/steps")
def add_step(
    family_id: int,
    body: AddStepRequest,
    db: Session = Depends(get_db),
    curator: User = Depends(require_role("curator")),
):
    family = get_family_for_curator(db, family_id, curator)
    catalog = get_catalog()
    service = catalog.services.get(body.service_id)
    if service is None:
        raise not_found(f"Услуга {body.service_id} не найдена в справочнике")
    plan = plans_service.add_step(db, family, curator.id, service)
    return plan.plan_json


@router.delete("/{family_id}/steps/{step_id}")
def delete_step(
    family_id: int,
    step_id: str,
    db: Session = Depends(get_db),
    curator: User = Depends(require_role("curator")),
):
    family = get_family_for_curator(db, family_id, curator)
    plan = plans_service.delete_step(db, family, curator.id, step_id)
    return plan.plan_json


@router.patch("/{family_id}/steps/{step_id}")
def patch_step(
    family_id: int,
    step_id: str,
    body: PatchStepRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("parent", "curator")),
):
    if user.role == "parent":
        family = get_family_for_parent(db, family_id, user)
    else:
        family = get_family_for_curator(db, family_id, user)
    plan = plans_service.patch_step_status(
        db, family, step_id, body.status, user.role, reason=body.reason, comment=body.comment
    )
    return plan.plan_json
