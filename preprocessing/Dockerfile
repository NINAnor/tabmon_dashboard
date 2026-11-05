FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH"
WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

COPY build_tables.py species_info.py species_ecology.py birdnet_multilingual.csv ./
COPY reference/ ./reference/
RUN python -c "import duckdb; c = duckdb.connect(); c.execute('INSTALL httpfs'); c.execute('INSTALL icu')"

ENV SOURCE=s3://bencretois-ns8129k-proj-tabmon \
    OUT=s3://bencretois-ns8129k-proj-tabmon/data/preprocessed/dashboard \
    DUCKDB_TEMP_DIR=/tmp/duckdb

# Needs S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY (and optionally S3_ENDPOINT).
CMD ["sh", "-c", "python build_tables.py --source \"$SOURCE\" --out \"$OUT\" --names birdnet_multilingual.csv"]
