FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

COPY tabmon_api/ /app/tabmon_api/
COPY data/ /app/data/

# Bake the DuckDB extension in so the container does not need to download it.
RUN python -c "import duckdb; duckdb.connect().execute('INSTALL httpfs')"

EXPOSE 8000
CMD ["uvicorn", "tabmon_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
