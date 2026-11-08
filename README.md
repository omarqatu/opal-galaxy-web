# Opal Galaxy — website (Wagtail)

Dynamic build of the Opal Galaxy Air Condition Trading L.L.C site. Content and design come from the approved static preview (`omarqatu/opal-static` v0.7); this repo replaces it once the client approves.

**Stack:** Django 5.2 LTS · Wagtail 7.0 LTS · PostgreSQL · gunicorn + WhiteNoise · Docker image on GHCR · Coolify.

## Structure
| Path | What it is |
|---|---|
| `catalog/` | Brands, product categories, the product × brand matrix (Wagtail snippets) |
| `core/` | Home page (with product and brand routes), service page, company settings, quote requests, seed command |
| `templates/`, `static/` | Markup and CSS carried over from the static preview |
| `seed/opal.json` + `seed/images/` | All site content; loaded into an empty database on first start |
| `entrypoint.sh` | Waits for the DB, migrates, seeds (once), creates the admin user (once), starts gunicorn |

## URLs
English at `/`, Arabic at `/ar/`. Pages: `/`, `/products/<slug>/`, `/brands/<slug>/`, `/maintenance/`. Admin: `/admin/`. Also `/robots.txt`, `/sitemap.xml`, `/health`. The quote form posts to `/quote/`.

## Environment
| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | yes | long random string |
| `DATABASE_URL` | yes | `postgres://user:pass@host:5432/db` (Coolify internal URL) |
| `ALLOWED_HOSTS` | yes | comma-separated domains |
| `CSRF_TRUSTED_ORIGINS` | yes | `https://<domain>` for each domain (form + admin) |
| `SITE_BASE_URL` | yes | `https://<domain>` — canonical, hreflang, sitemap |
| `SITE_NOINDEX` | — | default `1` (preview). Set `0` only after client approval |
| `N8N_QUOTE_WEBHOOK` | — | quote requests are POSTed here as JSON (always saved in the DB too) |
| `DJANGO_SUPERUSER_USERNAME` / `_PASSWORD` / `_EMAIL` | — | creates the admin once on first start |

Persistent volume: `/app/data` (uploaded images under `/app/data/media`).

## Local run
```bash
pip install -r requirements.txt
export DEBUG=1 DATABASE_URL=postgres://opal:opal@localhost:5432/opal
python manage.py migrate && python manage.py seed_site && python manage.py runserver
python manage.py test        # 10 tests: every page in both languages, quote form, noindex, sitemap
```

## Deploy
GitHub → Actions → **Run workflow**: tests on PostgreSQL → image to `ghcr.io/omarqatu/opal-galaxy-web` → Coolify deploy webhook.

Omar Digital · 2026
