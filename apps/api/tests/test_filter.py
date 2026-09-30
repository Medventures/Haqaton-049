from app.modules.engine.catalog import get_catalog
from app.modules.llm.filter import check_text


def test_diagnosis_wording_is_flagged():
    hits = check_text("У ребёнка выявлен диагноз аутизм", lang="ru")
    assert any(h["category"] == "diagnosis" for h in hits)


def test_allowlisted_service_name_not_flagged():
    hits = check_text("Рекомендуем центр поддержки детей с РАС", lang="ru")
    assert not hits


def test_clean_explanation_not_flagged():
    text = "Этот шаг — обследование в ПМПК. По итогам вы получите заключение с рекомендациями."
    assert check_text(text, lang="ru") == []


def test_treatment_wording_is_flagged():
    hits = check_text("Назначено лечение, препарат 5 мг", lang="ru")
    categories = {h["category"] for h in hits}
    assert "treatment" in categories


def test_all_catalog_explanation_templates_pass_filter():
    """К8 (раздел 20): в текстах плана нет формулировок диагноза.

    В режиме заглушки (раздел 12) объяснение шага — это explanation_template_*
    из справочника напрямую, без отдельного прогона через фильтр (шаблон
    уже считается безопасным текстом). Прогоняем фильтр по всем шаблонам
    здесь, чтобы гарантия была проверяемой, а не декларативной.
    """
    catalog = get_catalog()
    for service in catalog.services_list:
        for lang in ("ru", "kk"):
            text = service[f"explanation_template_{lang}"]
            hits = check_text(text, lang=lang)
            assert not hits, f"{service['service_id']} ({lang}): {hits}"
