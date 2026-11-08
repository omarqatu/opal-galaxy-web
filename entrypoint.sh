#!/bin/sh
# Start-up: fix volume ownership as root, then run everything as the unprivileged "app" user.
set -e
mkdir -p "$DATA_DIR/media"
chown -R app:app "$DATA_DIR"

as_app() { setpriv --reuid=app --regid=app --init-groups "$@"; }

as_app python manage.py migrate --noinput
as_app python manage.py seed_site          # no-op once the site has content

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  as_app python manage.py createsuperuser --noinput \
    --username "$DJANGO_SUPERUSER_USERNAME" --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" 2>/dev/null \
    || echo "Admin user already exists — skipped."
fi

exec setpriv --reuid=app --regid=app --init-groups \
  gunicorn opal.wsgi:application --bind 0.0.0.0:8000 \
  --workers "${WEB_CONCURRENCY:-2}" --timeout 60 --access-logfile -
