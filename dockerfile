# syntax=docker/dockerfile:1
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl build-essential && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --dev

COPY . .

CMD bash -lc 'if [ -d .git ]; then uv run pre-commit install && uv run pre-commit install --hook-type commit-msg; fi; uv run fastapi run app/main.py --port 8000 --host 0.0.0.0'
