# Деплой (раздел 2, 3 «Этап 5» SPEC.md)

Это инструкция для человека, который выполняет деплой — сам деплой в
это окружение не выполнялся (нет учётных данных Vercel/Render/Railway/
Fly/Supabase и сети до них из песочницы агента). Локально стек проверен
(см. `docs/PROGRESS.md`, «Этап 3»: живой смоук-тест через `next dev` +
`uvicorn`) и умеет собираться (`next build --webpack`, `docker build`
по `apps/api/Dockerfile` синтаксически корректен, но не собирался
здесь — нет `docker` в этой песочнице).

## 1. База данных — Supabase Postgres

1. Создать проект в Supabase, скопировать connection string.
2. `DATABASE_URL=postgresql+psycopg://...` (SQLAlchemy 2 диалект
   `psycopg`, пакет `psycopg[binary]` уже в `apps/api/requirements.txt`
   и импортируется без ошибок, но против живого Postgres не
   тестировался — в этом окружении нет доступного инстанса, см.
   `docs/OPEN_QUESTIONS.md`).
3. Миграции применяются автоматически при старте контейнера API
   (`CMD` в `Dockerfile` делает `alembic upgrade head` перед `uvicorn`).

## 2. API — любой хостинг с Docker (Render / Railway / Fly)

1. Собрать образ из корня репозитория: `docker build -f apps/api/Dockerfile -t aqylroute-api .`
2. Задать переменные окружения из `.env.example`: как минимум
   `DATABASE_URL`, `JWT_SECRET` (сгенерировать случайную строку 32+ байт,
   не оставлять дефолт из `config.py`), `OPENAI_API_KEY`/`OPENAI_MODEL`
   (иначе LLM-модуль работает в режиме заглушки, раздел 12), `MAIL_MODE`
   (`console` до подключения реального SMTP), `DEMO_MODE=true` и
   `DEMO_PASSWORD` на время демо, `API_URL` — публичный HTTPS-адрес
   самого API (для писем/ссылок).
3. Порт контейнера — `8000`. Нужен HTTPS (раздел 16: "Нужен HTTPS, иначе
   PWA не установится") — на Render/Railway/Fly он включён по умолчанию
   для публичного домена.
4. После деплоя один раз выполнить сид демо-данных (раздел 19.5):
   `docker exec <container> python -m app.seed`.

## 3. Web — Vercel

1. Импортировать `apps/web` как проект Next.js (Root Directory =
   `apps/web` в настройках Vercel, репозиторий монорепозиторный).
2. Переменная окружения `API_URL` = публичный HTTPS-адрес API из шага 2
   (используется в `next.config.ts` для rewrite `/api/*`).
3. Build command — по умолчанию `next build` из `apps/web/package.json`,
   который уже форсирует `--webpack` (см. `docs/DECISIONS.md`), это
   обязательно для генерации `public/sw.js` (раздел 16.2).
4. Vercel сам выдаёт HTTPS-домен — требование PWA выполняется автоматически.

## 3a. Альтернатива — один проект Vercel с сервисами

Корневой `vercel.json` описывает два сервиса: `web` (`apps/web`, Next.js,
публичный на `/`) и `api` (`apps/api`, FastAPI, публичный на `/api/*`).
Браузер ходит в `/api/*` того же домена, поэтому bindings не нужны, а
rewrite в `next.config.ts` на Vercel отключается (`process.env.VERCEL`).
Локально всё вместе запускается через `vercel dev`.

Ограничения, которые нужно проверить до выбора этого варианта:
- справочники из `data/` лежат вне `apps/api`; если они не попадут в
  бандл функции, задать `DATA_DIR` (см. `app/paths.py`);
- WeasyPrint (PDF, раздел 17) требует системных pango/cairo, которых нет
  в Python-рантайме Vercel;
- APScheduler (почасовой тик эскалации) в serverless не работает, нужен
  Vercel Cron;
- SQLite не подходит, нужен `DATABASE_URL` на Supabase; миграции
  (`alembic upgrade head`) и сид запускаются отдельно.

## 4. Чек-лист после деплоя (раздел 20)

Пройти чек-лист из раздела 20 SPEC.md на реальном публичном URL. Пункты,
которые нельзя было проверить в песочнице агента (нет браузера и
публичного HTTPS-адреса) — раздел «Этап 5» в `docs/PROGRESS.md` и
`docs/OPEN_QUESTIONS.md`.
