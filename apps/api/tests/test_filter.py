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
