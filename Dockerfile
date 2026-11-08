# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/app/data

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python tools/fetch_seed_assets.py \
 && SECRET_KEY=build-only python manage.py collectstatic --noinput \
 && useradd --uid 1000 --create-home app \
 && chmod +x entrypoint.sh

# Persistent data (SQLite database + uploaded images) lives in /app/data — mount a volume there.
EXPOSE 8000
CMD ["./entrypoint.sh"]
