# Прогресс

## Этап 0. Систематизация данных — готово

Что сделано:

- `docs/SPEC.md` — спецификация зафиксирована в репозитории.
- `AGENTS.md`, `CLAUDE.md` — одна строка со ссылкой на `docs/SPEC.md`.
- `docs/DECISIONS.md`, `docs/OPEN_QUESTIONS.md` — заведены и заполнены решениями/пробелами этапа 0.
- `.env.example` — переменные окружения из раздела 2 с пустыми/дефолтными значениями.
- `data/questions.json` — 18 вопросов банка (раздел 5), с `hint_ru`/`hint_kk`, `show_if`, `profile_field`, `priority`, `mandatory`, `order`, `source_ids`, `needs_review`.
- `data/services.json` — 15 услуг справочника (раздел 6), с документами, SLA, `age_window`, шаблонами объяснений на `ru`/`kk`, источниками и поставщиками.
- `data/document_types.json` — 10 типов документов (раздел 8).
- `data/providers.json` — поставщик `PRV_KAR_PMPK` (раздел 9.1).
- `data/sources.json` — 4 источника (раздел 9.2).
- `data/schemas/*.schema.json` — JSON Schema (draft-07) для всех пяти файлов выше.
- `apps/api/tests/test_data.py` — pytest-проверки этапа 0.
- `apps/api/requirements-dev.txt` — минимальные зависимости для прогона проверок этапа 0 (`pytest`, `jsonschema`).

Как проверить руками:

```bash
cd apps/api
python3 -m venv .venv          # если ещё не создан
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/test_data.py -v
```

Ожидаемый результат: все тесты зелёные (117 проверок на момент написания: 5 схем + по вопросу/услуге показатели + 1 проверка на 6 обязательных вопросов).

Проверки этапа (раздел 3, «Этап 0») покрыты тестами:

- [x] каждый файл проходит свою JSON Schema — `test_file_matches_schema`.
- [x] все ID в `show_if` существуют в `questions.json`, все коды вариантов в `show_if` существуют у соответствующего вопроса — `test_show_if_references_are_valid`.
- [x] каждый `profile_field` вопроса есть в схеме профиля из раздела 10 — `test_profile_field_is_known`.
- [x] все `predecessors_any` и документы услуг ссылаются на существующие `service_id` и `doc_type` — `test_service_predecessors_exist`, `test_service_documents_exist`.
- [x] у каждой услуги либо есть `source_ids`, либо `sla_verified: false` — `test_service_has_source_or_unverified_sla`.
- [x] в `questions.json` ровно 6 вопросов с `mandatory: true` — `test_exactly_six_mandatory_questions`.

Дополнительно (не требовалось явно, но проверено для целостности данных): ссылки услуг на существующие `provider_id` и `source_id`.

Известные открытые вопросы вынесены в `docs/OPEN_QUESTIONS.md` (13 услуг с `sla_verified: false`, возрастная граница `EDU_EARLY_HELP`, поставщики вне ПМПК, необходимость проверки казахских переводов носителем языка).

## Этап 1. Ядро API — не начат
## Этап 2. Сроки, эскалация, документы, уведомления, PDF — не начат
## Этап 3. Web: родитель и куратор — не начат
## Этап 4. PWA — не начат
## Этап 5. Демо и деплой — не начат
