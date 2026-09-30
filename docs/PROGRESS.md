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

## Этап 2. Сроки, эскалация, документы, уведомления, PDF — готово

Что сделано:

- `apps/api/app/modules/scheduler/escalation.py` — `recompute_family()`: просрочка, уровни эскалации 0-3 (раздел 11.3, каждый уровень пишется в `escalations` один раз на шаг), пересчёт сроков зависимых шагов, текст обращения уровня 3. Вызывается на каждый `GET /plans/{family}` и раз в час через APScheduler (`main.py`, best-effort — не критично для тестов).
- `apps/api/app/modules/documents/service.py` — загрузка документа, извлечение текста (`pdfplumber` для цифровых PDF), разбор через LLM (вызов 4), обновление `pmpk.valid_until`/`disability.review_date` в профиле при совпадении `doc_type`.
- `apps/api/app/modules/llm/` — `filter.py` (фильтр формулировок по `data/filter_patterns.json`), `cache.py` (SHA-256 кеш в `llm_cache`), `client.py` дополнен реальным вызовом OpenAI (structured outputs, `temperature=0`, `seed=42`) для вызовов 1-4 — включается только при непустом `OPENAI_API_KEY` (не покрыт тестами, см. `docs/OPEN_QUESTIONS.md`).
- `apps/api/app/modules/notifications/service.py` + `routers/notifications.py` — центр уведомлений и email-дубль через `outbox` при `MAIL_MODE=console`; события `draft_ready`, `plan_approved`, `red_flag`, `escalation_0..3` подключены.
- `apps/api/app/modules/reports/pdf.py` + `routers/reports.py` — три PDF-отчёта (`route`, `visit`, `summary`) на `ru`/`kk` через WeasyPrint, общий `base.css`, подпись "не является медицинским заключением" и дата формирования на каждой странице.
- `apps/api/app/routers/demo.py` — `POST /demo/time-shift` (абсолютный `offset_days`, не дельта — см. `docs/DECISIONS.md` не требовалось, значение уже соответствует таблице 19.3), `POST /demo/reset`, `GET /dev/mail`, все три только при `DEMO_MODE=true`.
- Найден и исправлен баг персистентности: мутация вложенных словарей в `plan_json`/`profile` "на месте" аліasилась с закешированным значением SQLAlchemy и UPDATE молча пропускался — см. `docs/DECISIONS.md`. Регрессия закрыта тестами с явным `db_session.expire_all()`.

Как проверить руками:

```bash
cd apps/api
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -v
```

Ожидаемый результат: 162 теста зелёные.

Проверки этапа (раздел 3, «Этап 2»):

- [x] сценарии сдвига времени из раздела 19.3 дают ожидаемые уровни эскалации и сроки — `tests/test_escalation.py` (все 6 строк таблицы, включая пересчёт срока S2).
- [x] загрузка тестового PDF заключения ПМПК обновляет `pmpk.valid_until` — `tests/test_documents.py` (реальный PDF собран через WeasyPrint и распарсен через `pdfplumber`, вызов 4 LLM замокан per раздел 12 "тесты всегда используют заглушку или мок").
- [x] все три PDF-отчёта генерируются на обоих языках — `tests/test_reports.py` (6 тестов: 3 отчёта × 2 языка).

Известные ограничения — в `docs/OPEN_QUESTIONS.md`: OCR сканов не реализован (нет `tesseract` в окружении), реальный OpenAI-путь не протестирован (нет ключа), `POST /demo/reset` не откатывает данные семей полностью.

## Этап 3. Web: родитель и куратор — готово (сокращённый охват экранов, см. ниже)

Что сделано:

- `apps/web/` — Next.js 16 (App Router), TypeScript, Tailwind v4, `next-intl` (`ru`/`kk` через `[locale]` сегмент и `middleware`→`proxy.ts`), rewrite `/api/*` → `API_URL` (раздел 13).
- Тёмная тема по умолчанию (раздел 15.3) через `@theme` в `app/globals.css`, IBM Plex Sans (`next/font/google`, кириллица + kk-буквы), `prefers-reduced-motion`, `.tap-target` (44×44), свои SVG-иконки ведомств и статусов (`components/icons.tsx`) — без сторонних наборов.
- Родитель: лендинг, вход, регистрация по инвайт-токену, интервью (один вопрос на экран, все 5 `answer_type`, прогресс, назад), ожидание черновика, план ("на этой неделе" + маршрут по ведомствам, просрочки со старым/новым сроком), карточка шага (документы, зависимости, источник, "Я сделал", PDF), документы (загрузка, список), уведомления.
- Куратор: список семей (проблемные сверху), карточка семьи и плана (подтвердить, добавить/убрать шаг из справочника, отметить `done`, видно `rule_id`/`needs_clarification`/`deadline_compressed`), просрочки.
- Backend: добавлен `GET /families/me` (нужен вебу, чтобы получить `family_id` родителя) и `GET /overdue` (раздел 13, был пропущен на этапе 2) — оба с тестами.
- **Живой смоук-тест** (не просто `next build`): подняты `uvicorn` + `next dev` с реальным rewrite, пройден полный путь curl-запросами через прокси — приглашение → регистрация → вход → интервью (все 6 обязательных вопросов в правильном фиксированном порядке + 2 опциональных) → `finish` строит черновик с настоящими шагами и объяснениями → родителю `404` пока `draft` → куратор подтверждает → родителю `200` → PDF-маршрут скачивается (`%PDF-1.7`, реальный файл). Это поймало настоящий баг (ниже).
- **Найден и исправлен баг** в `POST /auth/register`, не покрытый автотестами: SQLite возвращает `DateTime(timezone=True)` как naive после чтения из БД, сравнение с aware `datetime.now(timezone.utc)` падало `TypeError` → 500. Исправлено, добавлен `tests/test_auth.py`.

Как проверить руками (два терминала):

```bash
# терминал 1
cd apps/api && .venv/bin/python -m uvicorn app.main:app --reload
# терминал 2
cd apps/web && API_URL=http://localhost:8000 npm run dev
```
Открыть `http://localhost:3000/ru`.

Сокращения охвата (раздел 15) — по-честному не сделано, а не тихо пропущено:

- Экран «Граф» (визуализация зависимостей шагов через SVG), отдельные вкладки «Документы»/«Интервью»/«История» в кабинете куратора (раздел 15.2) объединены в одну страницу семьи вместо пяти отдельных вкладок — нужно для полного соответствия 15.2, но не блокирует ни один функциональный путь.
- Ответ родителя на «уточнение от куратора» нет в UI — сам backend-эндпоинт тоже неполный (см. `docs/OPEN_QUESTIONS.md`, отмечено на этапе 1-2).
- WCAG AA контраст и точные тайминги анимаций (<200 мс) не проаудированы инструментально — только базовые меры (`prefers-reduced-motion`, `.tap-target`).
- `PATCH /documents/{id}` (подтверждение полей, отметка «проверено») есть в API, но не подключён в UI документов (только загрузка и список).
- Установка PWA, офлайн, `manifest.ts`, `sw.ts` — предмет этапа 4, ниже.

## Этап 4. PWA — готово

Что сделано:

- `app/manifest.ts` — имя/описание на ru, `start_url=/?source=pwa`, `display=standalone`, тёмные `background_color`/`theme_color`, иконки 192/512/512-maskable/apple-touch-icon-180, `shortcuts` (План, Документы).
- Иконки сгенерированы скриптом `apps/api/scripts/generate_icons.py` (Pillow, без SVG-библиотек) — геометрический логотип (три узла маршрута + линия) в стиле проекта.
- `app/sw.ts` + `@serwist/next`: precache сборки + `/offline`, `CacheFirst` для статики (через `defaultCache` пресета Serwist для Next.js), `NetworkFirst` (7 дней, кеш `api-private`) для `GET /api/plans/*`, `/api/documents`, `/api/notifications`, `NetworkOnly` для остальных `/api/*` (включая все `POST/PATCH/DELETE` и `/api/reports/*`). PDF-эндпоинты дополнительно отдают `Cache-Control: no-store` (раздел 16.5).
- `components/AppChrome.tsx`: регистрация SW, кнопка «Установить» по `beforeinstallprompt` (скрыта на экране интервью), инструкция для iOS, баннер «Доступно обновление» (`skipWaiting` + reload), баннер офлайн, выход с `postMessage` в SW на очистку кеша `api-private`.
- `/[locale]/offline` — офлайн-страница (fallback для навигации).
- Интервью без сети не запускает `POST /interview/start`, показывает `common.needsInternet` вместо запроса.
- **Важно**: `@serwist/next` не поддерживает Turbopack (раздел 16.2 требует реальный service worker) — `npm run build` использует `next build --webpack` (см. `package.json`); `npm run dev` остаётся на Turbopack для скорости, но тогда `sw.js` не генерируется — PWA-проверки делать через `npm run build && npm run start`.

Как проверить руками:

```bash
cd apps/api && .venv/bin/python -m uvicorn app.main:app &
cd apps/web && API_URL=http://localhost:8000 npm run build && npm run start
```
Открыть `http://localhost:3000/ru`, DevTools → Application: манифест без ошибок, SW активен, `manifest.webmanifest`/`sw.js`/иконки отдаются 200 (проверено live curl'ом на `next start` в этой сессии).

Проверки раздела 16.6, не выполненные вручную в этом окружении (нет браузера/DevTools в песочнице): визуальная установка на Android/десктоп/iOS, реальное отключение сети в браузере с проверкой баннера на `/plan`, визуальная проверка Cache Storage после выхода. Логика этих трёх пунктов реализована (offline-баннер, `LOGOUT_CLEAR_PRIVATE_CACHE`, `NetworkFirst` fallback на `/offline`), но не подтверждена визуально — честно, а не тихо пропущено.

## Этап 5. Демо и деплой — готово (без фактического деплоя, см. ниже)

Что сделано:

- `apps/api/app/seed.py` (`python -m app.seed`) — раздел 19.5: применяет миграции, создаёт `curator@demo.kz`/`parent.a@demo.kz`/`parent.b@demo.kz` с паролем из `DEMO_PASSWORD`, семью А без интервью (для сцены), семью Б с пройденным интервью и подтверждённым планом по кейсу Б. Идемпотентен (второй запуск ничего не делает). Тесты — `tests/test_seed.py`.
- `apps/api/Dockerfile` — образ для любого Docker-хостинга (раздел 2), сохраняет структуру `apps/api/` + `data/` внутри контейнера (нужно `app/paths.py`), ставит системные библиотеки WeasyPrint, при старте гоняет `alembic upgrade head`. **Не собирался** — в этой песочнице нет `docker`.
- `docs/DEPLOY.md` — пошаговая инструкция: Supabase (БД) → API на Render/Railway/Fly через Docker → Web на Vercel (`Root Directory=apps/web`, `API_URL` env), с чек-листом переменных окружения.
- `psycopg[binary]` добавлен в `requirements.txt` для продакшен-Postgres (раздел 2) — импортируется без ошибок, но **не проверялся против живого Postgres** (SQLite использовался везде в тестах и локально).
- Три теста, закрывающие пробелы в проверяемости чек-листа раздела 20 (К7, К8, К16 для обоих кейсов) — см. таблицу ниже.
- **Найден ещё один баг** тестом на К8: kk-паттерн фильтра `дәрі` (лекарство) ложно срабатывал на `дәрігер` (врач) — обычное слово в шаблонах объяснений. Исправлено в `data/filter_patterns.json` (`дәрі(?!гер)`).

### Чек-лист приёмки (раздел 20)

Дальше — честный статус, не «всё готово». Пункты, требующие браузера или живого публичного HTTPS-URL, в этой песочнице не проверялись физически — только через юнит/интеграционные тесты и один живой смоук-тест (`uvicorn` + `next dev/start` на localhost, раздел «Этап 3»).

| № | Критерий | Статус | Как проверено |
| --- | --- | --- | --- |
| К1 | Публичная HTTPS-ссылка, демо без регистрации | ⬜ не проверено | Нет живого деплоя (нет учётных данных хостингов в этом окружении) |
| К2 | Интервью 8–12 вопросов | ✅ | `test_interview.py`, live-смоук |
| К3 | Набор вопросов зависит от ответов | ✅ | `test_interview.py::test_home_vs_school_...` |
| К4 | Приоритет/ответственный/срок/документы/статус; ≥2 ведомства | ✅ | `test_engine.py` |
| К5 | План одной JSON-структурой, детерминизм | ✅ | `test_engine.py::test_build_plan_is_deterministic` |
| К6 | Шаг вне справочника → 422 | ✅ | `test_api.py` |
| К7 | Объяснение на ru и kk у каждого шага | ✅ | `test_interview.py` (добавлено на этапе 5) |
| К8 | Нет формулировок диагноза в плане | ✅ | `test_filter.py::test_all_catalog_explanation_templates_pass_filter` (нашёл и исправил баг фильтра) |
| К9 | Статусы/правки переживают сессию | ✅ | `test_plans_patch.py` с `expire_all()` (поймали баг персистентности на этапе 2) |
| К10 | Просрочка видна с исходной/новой датой | ✅ (backend) / ⬜ (визуально) | `test_escalation.py`; фронтенд рисует `was/now`, не проверено в браузере |
| К11 | Эскалация 0–3 по таблице 19.3 | ✅ | `test_escalation.py`, все 6 строк |
| К12 | Права ролей, чужая семья недоступна | ✅ | `test_api.py` (несколько тестов изоляции) |
| К13 | Родитель не видит `draft` | ✅ | `test_api.py`, live-смоук |
| К14 | Куратор видит все просрочки на одном экране | ✅ | `test_overdue.py`, `/curator/overdue` |
| К15 | Стек Next.js/FastAPI/OpenAI/SQLite или Supabase | ✅ | в репозитории; Postgres-путь не тестировался живым инстансом |
| К16 | Оба кейса — полный цикл до эскалации 3 | ✅ | `test_escalation.py` (Б) + `test_case_a_escalation.py` (А, добавлено на этапе 5) |
| К17 | Установка PWA Android/десктоп/iOS | ✅ (артефакты) / ⬜ (визуально) | `manifest.webmanifest`/`sw.js`/иконки отданы 200 живым curl'ом; реальной установки в браузере не было |
| К18 | План родителя открывается без сети | ✅ (логика) / ⬜ (визуально) | `NetworkFirst`+`api-private` реализовано, не проверено выключением сети в браузере |
| К19 | После выхода приватный кеш удалён | ✅ (логика) / ⬜ (визуально) | `LOGOUT_CLEAR_PRIVATE_CACHE` реализовано и обработано в `sw.ts`, не проверено в DevTools |
| К20 | Тексты на ru и kk, казахские буквы корректны | ✅ | `messages/ru.json`+`kk.json` на все экраны, `IBM_Plex_Sans` с `cyrillic-ext`, живой curl подтвердил рендер kk-текста с ә/ғ/қ/ң/ө/ұ/ү/һ/і |

Итого: 15/20 подтверждено автоматически или живым локальным смоук-тестом,
5 пунктов (К1, К10/К17/К18/К19 частично) требуют реального браузера и/или
публичного HTTPS-деплоя, которых в этой песочнице нет — честно оставлено
как открытый пункт, а не заявлено как сделанное.

## Итог

Все пять этапов `docs/SPEC.md` реализованы: справочные данные и схемы,
движок правил, ядро API с авторизацией, интервью, планами и версиями,
сроки/эскалация/документы/уведомления/PDF, веб для родителя и куратора,
PWA, сид демо-данных и инструкция по деплою. 169 автотестов (`apps/api/tests/`)
зелёные. Известные пробелы и сокращения зафиксированы честно в этом файле,
`docs/DECISIONS.md` и `docs/OPEN_QUESTIONS.md`, а не скрыты — по правилу 3
раздела 0 SPEC.md.
