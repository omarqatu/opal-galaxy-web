# Opal Galaxy website — rules for Claude Code (cloud sessions)

## Who and what
- **Client:** Opal Galaxy Air Condition Trading L.L.C (Dubai). Opal is the sole owner of the site's content and data and approves look and content.
- **Operator:** Omar Qatu (Omar Digital), external contractor: admin, content, SEO, publishing, technical. Talk to Omar in **Arabic**; code, commits, PR text and docs in English.
- **Site:** Wagtail 7.0 LTS on Django 5.2 LTS, PostgreSQL 17, gunicorn + WhiteNoise, Docker image on GHCR, deployed by Coolify.
- **Staging:** https://new.opal-galaxy.com (noindex). The old static site still serves opal-galaxy.com.

## How work flows
1. Work happens in a Claude Code cloud session on a **new branch**. Never commit to `main`.
2. When the task is done and tests pass, push the branch and open a **pull request** with a clear summary.
3. GitHub Actions runs the full test suite on PostgreSQL 17 for the PR.
4. **Omar reviews and merges.** Never merge, and never ask for merge rights.
5. Omar deploys from GitHub: Actions → *Run workflow*. Deployment is never done from a session.

## Key files
- `opal-roadmap.md`: phases, done log, open decisions. Tick boxes and add to the done log in the same PR that finishes a task.
- `status.md`: short current status.
- `docs/mcp-spec.md`: Site MCP v1 specification (when added).
- `notes.md`: client feedback, one line per note with type (content, structure, images), tool used, status.
- `seed/opal.json` + `seed/images/`: initial content, loaded only into an empty database.

## Testing in the session: PostgreSQL 17 only
Production runs PostgreSQL 17, so tests run on PostgreSQL 17 too. **SQLite is not used**: it hides bugs that only PostgreSQL shows (constraints, ordering, JSON, text search).

At the start of every session, start PostgreSQL 17 with Docker, using the same image as CI and production (`postgres:17-alpine`):
```bash
docker run -d --name opal-pg -p 5432:5432 \
  -e POSTGRES_USER=opal -e POSTGRES_PASSWORD=opal -e POSTGRES_DB=opal \
  postgres:17-alpine
until docker exec opal-pg pg_isready -U opal; do sleep 1; done
pip install -r requirements.txt
```
If Docker is unavailable, install `postgresql-17` from `apt.postgresql.org` instead. Do not use other PostgreSQL distributions (npm packages, embedded binaries).

Then:
```bash
export DEBUG=1 DATA_DIR=/tmp/data DATABASE_URL=postgres://opal:opal@localhost:5432/opal
python manage.py test --noinput
python manage.py makemigrations --check --dry-run
```
Confirm the version through Django's own connection (`SELECT version()`), which must report 17.x. If PostgreSQL 17 cannot be installed in the session, **stop and tell Omar**; do not fall back to SQLite. The PR's GitHub Actions run (the `test` job in `deploy.yml`, PostgreSQL 17) must also be green before the PR is ready.

## Rules
1. **Tests before every push, on PostgreSQL 17.** Both commands above must pass. Add tests for every new behaviour. The PR description states the PostgreSQL version the tests ran on.
2. **Never without Omar's explicit approval in the task:** switching the main domain, setting `SITE_NOINDEX=0`, DNS changes, deleting anything, changing the deploy workflow's secrets or triggers.
3. **Secrets:** never print, log or commit tokens, passwords or `DATABASE_URL` values. There are no secrets in the session and none are needed.
4. **Migrations** must be safe on existing production data; data migrations get a test.
5. **Content rules (Opal):** formal Modern Standard Arabic (no colloquial); English is the default language and every text has both; model names, capacities and refrigerants copied exactly as the manufacturer writes them; Carrier = every series on Carrier's official Gulf site, R22 included; Coolex = only catalogues Omar supplies; unconfirmed ranges are marked "confirmed on the quote"; the founder's name never appears on the site.
6. **Pin dependencies** to released versions at least two weeks old.
7. **Keep PRs small:** one task per PR. If a task grows, stop and propose a split.
8. **PR description:** what changed, why, test results, anything Omar must check on staging after deploy, and a short Arabic summary at the end for Omar.
