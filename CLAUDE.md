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

## Testing in the session
```bash
pip install -r requirements.txt
# Quick check on SQLite (no database server needed in the session):
DEBUG=1 DATA_DIR=/tmp/data python manage.py test --noinput
DEBUG=1 DATA_DIR=/tmp/data python manage.py makemigrations --check --dry-run
```
If PostgreSQL is available in the session, also run the tests with
`DATABASE_URL=postgres://...`. The PR's GitHub Actions run on PostgreSQL 17 is the final check; a PR is ready only when it is green.

## Rules
1. **Tests before every push.** Both commands above must pass. Add tests for every new behaviour. Nothing PostgreSQL-specific may break SQLite tests without a note in the PR.
2. **Never without Omar's explicit approval in the task:** switching the main domain, setting `SITE_NOINDEX=0`, DNS changes, deleting anything, changing the deploy workflow's secrets or triggers.
3. **Secrets:** never print, log or commit tokens, passwords or `DATABASE_URL` values. There are no secrets in the session and none are needed.
4. **Migrations** must be safe on existing production data; data migrations get a test.
5. **Content rules (Opal):** formal Modern Standard Arabic (no colloquial); English is the default language and every text has both; model names, capacities and refrigerants copied exactly as the manufacturer writes them; Carrier = every series on Carrier's official Gulf site, R22 included; Coolex = only catalogues Omar supplies; unconfirmed ranges are marked "confirmed on the quote"; the founder's name never appears on the site.
6. **Pin dependencies** to released versions at least two weeks old.
7. **Keep PRs small:** one task per PR. If a task grows, stop and propose a split.
8. **PR description:** what changed, why, test results, anything Omar must check on staging after deploy, and a short Arabic summary at the end for Omar.
