FROM astral/uv:python3.13-bookworm-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN apt-get update && apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 shared-mime-info poppler-utils && rm -rf /var/lib/apt/lists/*
ARG UV_NO_DEV=1
RUN uv sync --locked
COPY . .
ENV PATH="/app/.venv/bin:$PATH"
ENV WEB_CONCURRENCY=3
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "conexiones.wsgi:application"]
