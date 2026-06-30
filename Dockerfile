# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY tools ./tools
COPY alembic ./alembic
COPY alembic.ini ./

FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

RUN groupadd --system mailcraft && useradd --system --gid mailcraft mailcraft

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app ./app
COPY --from=builder /app/tools ./tools
COPY --from=builder /app/alembic ./alembic
COPY --from=builder /app/alembic.ini ./alembic.ini
COPY pyproject.toml uv.lock ./
COPY scripts/deploy.sh ./scripts/deploy.sh

RUN chmod +x ./scripts/deploy.sh \
    && mkdir -p /app/data/uploads \
    && chown -R mailcraft:mailcraft /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8081

EXPOSE 8081

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8081/api/health')" || exit 1

USER mailcraft

CMD ["./scripts/deploy.sh"]
