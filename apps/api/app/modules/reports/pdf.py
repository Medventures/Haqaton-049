"""PDF-отчёты (раздел 17 SPEC.md). Рендер через WeasyPrint, данные
подставляет код, LLM не используется, ИИН не выводится."""
from datetime import datetime, timezone
from html import escape

from app.paths import REPO_ROOT

CSS_PATH = REPO_ROOT / "apps" / "api" / "app" / "templates" / "reports" / "base.css"

_L = {
    "ru": {
        "route_title": "Маршрут семьи",
        "visit_title": "Памятка на визит",
        "summary_title": "Выписка по семье",
        "step": "Шаг",
        "deadline": "Срок",
        "status": "Статус",
        "responsible": "Ответственный",
        "documents": "Документы",
        "explanation": "Объяснение",
        "provider": "Поставщик",
        "based_on": "На основании",
        "versions": "Версии плана",
        "overdue": "Просрочки и эскалации",
        "generated": "Дата формирования",
    },
    "kk": {
        "route_title": "Отбасы маршруты",
        "visit_title": "Барар алдындағы жадынама",
        "summary_title": "Отбасы бойынша үзінді",
        "step": "Қадам",
        "deadline": "Мерзім",
        "status": "Мәртебе",
        "responsible": "Жауапты",
        "documents": "Құжаттар",
        "explanation": "Түсіндірме",
        "provider": "Қызмет көрсетуші",
        "based_on": "Негіз",
        "versions": "Жоспар нұсқалары",
        "overdue": "Мерзімі өткендер мен эскалациялар",
        "generated": "Қалыптастырылған күні",
    },
}


def _wrap(title: str, body_html: str, lang: str) -> str:
    gen = datetime.now(timezone.utc).date().isoformat()
    t = _L[lang]
    return f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<style>{CSS_PATH.read_text(encoding='utf-8')}</style>
</head><body>
<div class="gen-date">{t['generated']}: {gen}</div>
<h1>{escape(title)}</h1>
{body_html}
</body></html>"""


def _step_html(step: dict, catalog, lang: str) -> str:
    t = _L[lang]
    title = step.get(f"title_{lang}") or step["service_id"]
    docs = "".join(f"<li>{escape(d['doc_type'])} ({escape(d['kind'])}{', есть' if d['in_wallet'] else ''})</li>" for d in step.get("documents", []))
    sources = ", ".join(step.get("source_ids") or []) or "—"
    explanation = step.get(f"explanation_{lang}") or ""
    return f"""<div class="step">
<h3>{escape(title)}</h3>
<div class="meta">{t['deadline']}: {escape(step.get('deadline') or '—')} · {t['status']}: {escape(step['status'])} · {t['responsible']}: {escape(step['responsible'])}</div>
<p>{escape(explanation)}</p>
<div class="doc-list"><strong>{t['documents']}:</strong><ul>{docs}</ul></div>
<div class="meta">{t['based_on']}: {escape(sources)}</div>
</div>"""


def render_route_html(plan_json: dict, catalog, lang: str) -> str:
    t = _L[lang]
    by_agency: dict[str, list] = {"medicine": [], "education": [], "social": []}
    for step in plan_json["steps"]:
        by_agency.setdefault(step["agency"], []).append(step)
    body = ""
    for agency, steps in by_agency.items():
        if not steps:
            continue
        body += f"<h2>{escape(agency)}</h2>" + "".join(_step_html(s, catalog, lang) for s in steps)
    return _wrap(t["route_title"], body, lang)


def render_visit_html(step: dict, catalog, lang: str) -> str:
    t = _L[lang]
    service = catalog.services.get(step["service_id"], {})
    providers = [catalog.providers[pid] for pid in step.get("provider_ids", []) if pid in catalog.providers]
    provider_html = ""
    for p in providers:
        provider_html += f"""<p><strong>{t['provider']}:</strong> {escape(p['name_ru'] if lang=='ru' else p['name_kk'])}<br>
{escape(p['address_ru'] if lang=='ru' else p['address_kk'])} · {escape(p['phone'])}<br>
{escape(', '.join(p['booking_methods']))}</p>"""
    body = _step_html(step, catalog, lang) + provider_html
    return _wrap(t["visit_title"], body, lang)


def render_summary_html(family_child_name: str, plan_json: dict, versions: list, escalations: list, documents: list, lang: str) -> str:
    t = _L[lang]
    steps_html = "".join(_step_html(s, None, lang) for s in plan_json["steps"])
    versions_rows = "".join(
        f"<tr><td>{v['version']}</td><td>{escape(v['status'])}</td><td>{escape(v['created_by'])}</td></tr>" for v in versions
    )
    escalations_rows = "".join(
        f"<tr><td>{escape(e['step_id'])}</td><td>{e['level']}</td></tr>" for e in escalations
    )
    documents_rows = "".join(
        f"<tr><td>{escape(d['doc_type'])}</td><td>{escape(d.get('valid_until') or '—')}</td></tr>" for d in documents
    )
    body = f"""<p>{escape(family_child_name)}</p>
{steps_html}
<h2>{t['versions']}</h2>
<table><tr><th>#</th><th>{t['status']}</th><th>by</th></tr>{versions_rows}</table>
<h2>{t['overdue']}</h2>
<table><tr><th>{t['step']}</th><th>level</th></tr>{escalations_rows}</table>
<h2>{t['documents']}</h2>
<table><tr><th>doc_type</th><th>valid_until</th></tr>{documents_rows}</table>
"""
    return _wrap(t["summary_title"], body, lang)


def html_to_pdf(html: str) -> bytes:
    from weasyprint import HTML

    return HTML(string=html, base_url=str(REPO_ROOT)).write_pdf()
