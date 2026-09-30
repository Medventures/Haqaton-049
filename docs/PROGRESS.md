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

## Этап 1. Ядро API — готово

Что сделано:

- `data/fixtures/case_a.json`, `case_b.json` — фикстуры раздела 19.1/19.2 (`answers`, `profile_expected`, `expected_steps`).
- `apps/api/app/modules/engine/` — движок правил: `rules.py` (R01-R15), `engine.py` (`build_plan`, чистая функция), `catalog.py` (загрузка и валидация `data/*.json` в память при старте).
- `apps/api/app/models.py` + `apps/api/alembic/` — все 14 таблиц раздела 14, начальная миграция `0001_initial`.
- `apps/api/app/auth.py` — пароли (`pbkdf2_hmac`, без внешних зависимостей), JWT в httpOnly cookie (`PyJWT`), `require_role()`.
- `apps/api/app/clock.py` — единственный источник "сегодня" (`Asia/Almaty` + `settings.time_offset_days`), прямых `date.today()` в коде нет.
- `apps/api/app/modules/llm/` — маскирование (`masking.py`) и режим заглушки (`stub.py`, `client.py`) для вызовов 1-3; реальный OpenAI — этап 2 (см. `docs/DECISIONS.md`).
- `apps/api/app/modules/interview/` — `flow.py` (show_if, валидация ответа, следующий вопрос, профиль, unknown_fields — чистые функции) и `service.py` (оркестрация поверх БД: start/answer/back/finish).
- `apps/api/app/modules/plans/` — `service.py` (версии, черновик, подтверждение, добавление/удаление шага) и `transitions.py` (переходы статуса шага, раздел 11.4).
- `apps/api/app/routers/` — `auth`, `interview`, `plans`, `catalog`, `families`; `apps/api/app/main.py` — сборка приложения, единый формат ошибок `{"error": {...}}`.
- `apps/api/requirements.txt` / `requirements-dev.txt` — обновлены под полный стек этапа 1.
- Тесты: `tests/test_engine.py` (фикстуры + детерминизм), `tests/test_api.py` (роли, приватность `draft`, изоляция семей, 422 на несуществующий `service_id`), `tests/test_interview.py` (интеграционный прогон интервью через LLM-заглушку).

Как проверить руками:

```bash
cd apps/api
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -v
```

Ожидаемый результат: 138 тестов зелёные (плюс 117 из `test_data.py` — итого 255 в `apps/api/tests/`).

Проверки этапа (раздел 3, «Этап 1») покрыты тестами:

- [x] автотесты по фикстурам из раздела 19 дают ровно ожидаемые планы — `test_engine.py::test_build_plan_matches_expected_steps` (кейсы А и Б, все поля таблиц 19.1/19.2 совпадают побайтно).
- [x] повторный прогон даёт побайтно одинаковый `steps` — `test_engine.py::test_build_plan_is_deterministic`.
- [x] попытка добавить шаг с несуществующим `service_id` возвращает 422 — `test_api.py::test_add_step_with_unknown_service_id_returns_422` (через `Literal[...]` из каталога в Pydantic-схеме запроса).
- [x] родитель не может получить план в статусе `draft` — `test_api.py::test_parent_cannot_see_draft_plan`.
- [x] родитель не может получить план чужой семьи (доп. проверка К12/К13) — `test_api.py::test_parent_cannot_access_another_familys_plan`, `test_curator_cannot_access_another_curators_family`.

Дополнительно проверено вручную логикой (не входит в обязательный список этапа 1, но нужно для К2/К3): интервью задаёт от 8 до 12 вопросов, все 6 обязательных всегда заданы, набор вопросов зависит от `Q03` (`home` открывает Q09, `school` — нет) — `tests/test_interview.py`.

Известные ограничения зафиксированы в `docs/DECISIONS.md` и `docs/OPEN_QUESTIONS.md`: версии плана создаются только на 3 события (черновик/правка/подтверждение), LLM-модуль только в режиме заглушки, ответ родителя на "уточнение от куратора" не реализован (нужен для этапа 2 вместе с уведомлениями).

## Этап 2. Сроки, эскалация, документы, уведомления, PDF — не начат
## Этап 3. Web: родитель и куратор — не начат
## Этап 4. PWA — не начат
## Этап 5. Демо и деплой — не начат
