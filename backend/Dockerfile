FROM python:3.14-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /bin/

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./

FROM base AS development
RUN uv sync --frozen
COPY backend/app ./app
COPY backend/cypher ./cypher
COPY backend/tests ./tests
EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production
RUN uv sync --frozen --no-dev

COPY backend/app ./app
COPY backend/cypher ./cypher

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
