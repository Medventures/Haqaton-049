# Всё-в-одном для быстрого демо (Render Blueprint, см. render.yaml):
# Next.js (apps/web) + FastAPI (apps/api) + SQLite в одном контейнере.
# Основной вариант деплоя — docs/DEPLOY.md.

FROM node:22-slim AS web
WORKDIR /repo/apps/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
# Rewrite /api/* вшивается на сборке: API в том же контейнере.
ENV API_URL=http://127.0.0.1:8000
RUN npm run build

FROM python:3.11-slim
# Системные библиотеки WeasyPrint (раздел 17) и шрифты для кириллицы/kk.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libcairo2 \
    fonts-liberation fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
COPY --from=web /usr/local/bin/node /usr/local/bin/node

WORKDIR /repo
COPY apps/api/requirements.txt apps/api/requirements.txt
RUN pip install --no-cache-dir -r apps/api/requirements.txt

COPY apps/api/ apps/api/
COPY data/ data/
COPY --from=web /repo/apps/web apps/web
COPY deploy/start.sh deploy/start.sh

ENV PORT=10000
EXPOSE 10000
CMD ["sh", "deploy/start.sh"]
