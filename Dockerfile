FROM astral/uv:python3.13-bookworm-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN apt-get update && apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 shared-mime-info poppler-utils && rm -rf /var/lib/apt/lists/*
RUN uv sync
COPY . .
RUN mv entrypoint.sh /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh
EXPOSE 8000
ENTRYPOINT ["entrypoint.sh"]
CMD uv run gunicorn --workers $((2 * $(nproc) + 1)) --bind 0.0.0.0:8000 conexiones.wsgi:application
