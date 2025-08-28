# syntax=docker/dockerfile:1.7

############################
# Base: cài uv + sync deps #
############################
FROM python:3.11-slim AS base
# Cài uv theo hướng dẫn chính thức (copy binary)
COPY --from=ghcr.io/astral-sh/uv:0.8.13 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy file cấu hình deps trước để cache
COPY pyproject.toml uv.lock ./
# Cài dependency trước, CHƯA copy source (tối ưu cache)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Copy source vào container
ADD . /app
# Cài project vào venv /.venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

################################
# Dev: dùng fastapi dev + reload
################################
FROM base AS dev
EXPOSE 8000
# Bind 0.0.0.0 để truy cập từ host
CMD ["uv", "run", "fastapi", "dev", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]

################################
# Prod: fastapi run (no reload)
################################
FROM python:3.11-slim AS prod
# Cần uv ở final stage nếu dùng `uv run`
COPY --from=ghcr.io/astral-sh/uv:0.8.13 /uv /uvx /bin/
WORKDIR /app
COPY --from=base /app /app
# Trỏ PATH vào venv để gọi công cụ trong môi trường đã sync
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uv", "run", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
