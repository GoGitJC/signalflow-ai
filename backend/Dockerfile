# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml alembic.ini ./
COPY app ./app
COPY alembic ./alembic

# ---------------------------------------------------------------------------
# development / test — includes pytest, ruff, mypy (optional [dev] extras)
# ---------------------------------------------------------------------------
FROM base AS development

COPY tests ./tests

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir ".[dev]"

# Overridden by `docker compose run --rm backend-test <cmd>`
CMD ["pytest"]

# ---------------------------------------------------------------------------
# production — runtime only (default final stage)
# ---------------------------------------------------------------------------
FROM base AS production

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
