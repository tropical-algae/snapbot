FROM python:3.13-slim-bookworm AS builder

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN --mount=from=ghcr.io/astral-sh/uv:0.11.21,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    UV_LINK_MODE=copy uv sync --locked --no-dev --no-editable


FROM python:3.13-slim-bookworm

ENV PATH=/app/.venv/bin:${PATH} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/src ./src
COPY plugins ./plugins

CMD ["ncatbot", "run", "--non-interactive", "--no-hot-reload", "--plugins-dir", "/app/plugins"]
