FROM python:3.13-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /uvx /bin/
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN apt-get update && apt-get install -y --no-install-recommends libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 shared-mime-info poppler-utils && rm -rf /var/lib/apt/lists/*
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd --gid "$APP_GID" app && useradd --uid "$APP_UID" --gid app --create-home app
ARG UV_NO_DEV=1
ENV UV_COMPILE_BYTECODE=1
RUN uv sync --locked
COPY . .
RUN mkdir -p /app/media /app/staticfiles && chown app:app /app/media /app/staticfiles
ENV PATH="/app/.venv/bin:$PATH"
ENV WEB_CONCURRENCY=3
USER app
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "conexiones.wsgi:application"]
