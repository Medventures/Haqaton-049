# Раздел 2 SPEC.md: "API на любом хостинге с Docker (Render, Railway, Fly)".
# Собирается из корня репозитория: docker build -f apps/api/Dockerfile .
FROM python:3.11-slim-bookworm

# Системные библиотеки WeasyPrint (раздел 17) и шрифты для кириллицы/kk.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libcairo2 \
    fonts-liberation fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Сохраняем ту же относительную структуру apps/api + data/, что и в
# репозитории — app/paths.py вычисляет REPO_ROOT через parents[3].
WORKDIR /app

COPY apps/api/requirements.txt apps/api/requirements.txt
RUN pip install --no-cache-dir -r apps/api/requirements.txt

COPY apps/api/ apps/api/
COPY data/ data/

WORKDIR /app/apps/api
EXPOSE 8000

CMD ["sh", "-c", "python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
