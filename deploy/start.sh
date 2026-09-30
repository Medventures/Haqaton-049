#!/bin/sh
# Запуск всё-в-одном: миграции, сид демо (идемпотентен), API на 8000,
# web на $PORT (единственный публичный порт).
set -e

# Ссылки в письмах и флаг secure у cookie берутся из API_URL — это
# публичный адрес сайта (Render сам выставляет RENDER_EXTERNAL_URL).
export API_URL="${API_URL:-${RENDER_EXTERNAL_URL:-http://localhost:$PORT}}"

cd /repo/apps/api
python -m alembic upgrade head
python -m app.seed
uvicorn app.main:app --host 127.0.0.1 --port 8000 &

cd /repo/apps/web
API_URL=http://127.0.0.1:8000 exec node node_modules/next/dist/bin/next start -H 0.0.0.0 -p "$PORT"
