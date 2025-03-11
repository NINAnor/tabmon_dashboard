FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_LINK_MODE=copy

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

ADD src/ /app/src
ADD .streamlit/ /app/.streamlit

CMD ["uv", "run", "streamlit", "run", "--server.headless", "true", "--server.address", "0.0.0.0", "src/app.py"]
