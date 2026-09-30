from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth import require_role
from app.db import get_db
from app.deps import get_family_for_curator, get_family_for_parent
from app.errors import bad_request, not_found
from app.models import CasePlan, Document, Escalation, User
from app.modules.engine.catalog import get_catalog
from app.modules.plans.service import get_latest_plan
from app.modules.reports.pdf import html_to_pdf, render_route_html, render_summary_html, render_visit_html

router = APIRouter(prefix="/reports", tags=["reports"])


def _get_family(db, family_id, user):
    if user.role == "parent":
        return get_family_for_parent(db, family_id, user)
    return get_family_for_curator(db, family_id, user)


@router.get("/route/{family_id}.pdf")
def report_route(
    family_id: int,
    lang: str = Query("ru", pattern="^(ru|kk)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("parent", "curator")),
):
    family = _get_family(db, family_id, user)
    plan = get_latest_plan(db, family.id)
    if plan is None or (user.role == "parent" and plan.status == "draft"):
        raise not_found("План не найден")
    html = render_route_html(plan.plan_json, get_catalog(), lang)
    # Раздел 16.5: файлы документов и PDF — Cache-Control: no-store.
    return Response(content=html_to_pdf(html), media_type="application/pdf", headers={"Cache-Control": "no-store"})


@router.get("/visit/{family_id}.pdf")
def report_visit(
    family_id: int,
    step: str = Query(...),
    lang: str = Query("ru", pattern="^(ru|kk)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("parent", "curator")),
):
    family = _get_family(db, family_id, user)
    plan = get_latest_plan(db, family.id)
    if plan is None or (user.role == "parent" and plan.status == "draft"):
        raise not_found("План не найден")
    step_obj = next((s for s in plan.plan_json["steps"] if s["step_id"] == step), None)
    if step_obj is None:
        raise bad_request(f"Шаг {step} не найден")
    html = render_visit_html(step_obj, get_catalog(), lang)
    # Раздел 16.5: файлы документов и PDF — Cache-Control: no-store.
    return Response(content=html_to_pdf(html), media_type="application/pdf", headers={"Cache-Control": "no-store"})


@router.get("/summary/{family_id}.pdf")
def report_summary(
    family_id: int,
    lang: str = Query("ru", pattern="^(ru|kk)$"),
    db: Session = Depends(get_db),
    curator: User = Depends(require_role("curator")),
):
    family = get_family_for_curator(db, family_id, curator)
    plan = get_latest_plan(db, family.id)
    if plan is None:
        raise not_found("План не найден")
    versions = [
        {"version": p.version, "status": p.status, "created_by": p.created_by}
        for p in db.query(CasePlan).filter(CasePlan.family_id == family.id).order_by(CasePlan.version).all()
    ]
    escalations = [
        {"step_id": e.step_id, "level": e.level}
        for e in db.query(Escalation).filter(Escalation.family_id == family.id).all()
    ]
    documents = [
        {"doc_type": d.doc_type, "valid_until": d.valid_until}
        for d in db.query(Document).filter(Document.family_id == family.id).all()
    ]
    html = render_summary_html(family.child_name, plan.plan_json, versions, escalations, documents, lang)
    # Раздел 16.5: файлы документов и PDF — Cache-Control: no-store.
    return Response(content=html_to_pdf(html), media_type="application/pdf", headers={"Cache-Control": "no-store"})
