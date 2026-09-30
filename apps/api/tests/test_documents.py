"""Раздел 8, этап 2 проверка: загрузка тестового PDF заключения ПМПК
обновляет pmpk.valid_until. Раздел 12: "Тесты всегда используют заглушку
или мок" — вызов 4 (разбор документа) мокается, реальный OpenAI не
задействован.
"""
import io

from app.models import Interview
from app.modules.documents import service as documents_service
from tests.conftest import login, make_curator, make_family, make_parent


def _sample_pmpk_pdf_bytes() -> bytes:
    from weasyprint import HTML

    html = """<html><body>
    <h1>Заключение ПМПК</h1>
    <p>Ребёнок: [CHILD]</p>
    <p>Рекомендовано: педагог-ассистент</p>
    <p>Заключение действительно до: 2027-03-15</p>
    </body></html>"""
    return HTML(string=html).write_pdf()


def test_pdf_upload_updates_pmpk_valid_until(client, db_session, monkeypatch):
    curator = make_curator(db_session)
    parent = make_parent(db_session)
    family = make_family(db_session, curator, parent)

    interview = Interview(family_id=family.id, answers=[], profile={"pmpk": {"status": "valid", "valid_until": None}}, unknown_fields=[])
    db_session.add(interview)
    db_session.commit()

    def fake_parse_document(text, db=None):
        assert "[CHILD]" in text or "CHILD" in text  # маскирование прошло раньше при необходимости
        return {
            "doc_type": "pmpk_conclusion",
            "issued_at": "2026-03-15",
            "valid_until": "2027-03-15",
            "issuer": "ПМПК",
        }

    monkeypatch.setattr(documents_service.llm_client, "parse_document", fake_parse_document)

    login(client, parent.email)
    pdf_bytes = _sample_pmpk_pdf_bytes()
    resp = client.post(
        "/api/documents",
        files={"file": ("pmpk.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["doc_type"] == "pmpk_conclusion"
    assert body["valid_until"] == "2027-03-15"

    db_session.refresh(interview)
    assert interview.profile["pmpk"]["valid_until"] == "2027-03-15"


def test_extract_text_reads_real_pdf_content():
    pdf_bytes = _sample_pmpk_pdf_bytes()
    text = documents_service._extract_text(pdf_bytes, "application/pdf")
    assert "Заключение ПМПК" in text
    assert "2027-03-15" in text
