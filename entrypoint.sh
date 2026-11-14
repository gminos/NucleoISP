#!/bin/bash

set -e

if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "se empieza a aplicar migraciones"
    chown -R $(stat -c '%u:%g' /app) /app/.venv 2>/dev/null || true
    uv run python manage.py migrate_schemas --shared
    uv run python manage.py migrate_schemas --tenant

    echo "generando los archivo estaticos... calmado"
    uv run python manage.py collectstatic --noinput --verbosity 0
fi

echo "se va a iniciar el servidor Django"
exec "$@"
