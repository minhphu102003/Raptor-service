# syntax=docker/dockerfile:1.7

############################
# Base: Install uv + sync deps #
############################
FROM python:3.11-slim AS base
# Install uv according to official instructions (copy binary)
COPY --from=ghcr.io/astral-sh/uv:0.8.13 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependency files first to optimize cache
COPY pyproject.toml uv.lock ./


# Install dependencies first, WITHOUT copying source (optimize cache)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Copy source into container
ADD . /app
# Install project into venv /.venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

################################
# Dev: use fastapi dev + reload
################################
FROM base AS dev
EXPOSE 8000
# Bind 0.0.0.0 to access from host
# nosec B104 - This is for local development only
CMD ["uv", "run", "fastapi", "dev", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]

################################
# Prod: fastapi run (no reload)
################################
FROM python:3.11-slim AS prod
# Need uv in final stage if using `uv run`
COPY --from=ghcr.io/astral-sh/uv:0.8.13 /uv /uvx /bin/
WORKDIR /app
COPY --from=base /app /app
# Point PATH to venv to call tools in synced environment
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
# nosec B104 - This is for containerized deployment
CMD ["uv", "run", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]

################################
# Test: for running tests
################################
FROM base AS test
# Install test dependencies if any
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --extra test

# Run tests
CMD ["uv", "run", "pytest"]
