# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/app/data MEDIA_ROOT=/app/data/media
WORKDIR /app

# libjpeg/libwebp for Wagtail image renditions (Pillow wheels bundle them; kept slim otherwise)
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN SECRET_KEY=build-only python manage.py collectstatic --noinput -v0 \
 && useradd --uid 1000 --create-home app \
 && mkdir -p /app/data/media && chown -R app:app /app/data \
 && chmod +x /app/entrypoint.sh

USER app
EXPOSE 8000
VOLUME ["/app/data"]
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "opal.wsgi:application", "-b", "0.0.0.0:8000", "--workers", "2", "--threads", "4", \
     "--access-logfile", "-", "--timeout", "60"]
