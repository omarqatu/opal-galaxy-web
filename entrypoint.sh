#!/bin/sh
# Prepare the database on every start: wait for it, migrate, seed an empty site,
# create the admin user once (if env vars are set), then start the server.
set -e

python - <<'PY'
import os, sys, time
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opal.settings")
django.setup()
from django.db import connection
for i in range(30):
    try:
        connection.ensure_connection(); break
    except Exception as e:  # database container may still be starting
        print(f"waiting for database ({i+1}/30): {e.__class__.__name__}", flush=True); time.sleep(2)
else:
    sys.exit("database not reachable")
PY

python manage.py migrate --noinput
python manage.py seed_site            # no-op once the site has content

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
U = get_user_model(); n = os.environ['DJANGO_SUPERUSER_USERNAME']
if not U.objects.filter(username=n).exists():
    U.objects.create_superuser(n, os.environ.get('DJANGO_SUPERUSER_EMAIL', ''), os.environ['DJANGO_SUPERUSER_PASSWORD'])
    print('admin user created:', n)
"
fi

exec "$@"
