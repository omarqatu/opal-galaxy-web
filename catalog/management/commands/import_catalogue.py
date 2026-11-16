"""manage.py import_catalogue <file.json> [--apply]

Dry run by default: validates the file, prints the per-row diff (current → proposed) and
writes review/<brand>-review.md. With --apply, the changes are saved as unpublished
draft revisions of the affected product categories. Nothing is ever published.
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalog.importer import ImportFileError, apply_plan, build_plan, diff_lines, review_markdown


class Command(BaseCommand):
    help = "Import one brand's catalogue rows from JSON as draft revisions (dry run unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument("file")
        parser.add_argument("--apply", action="store_true", help="Write unpublished drafts (never publishes)")
        parser.add_argument("--review-dir", default=str(Path(settings.BASE_DIR) / "review"))

    def handle(self, *args, file, apply, review_dir, **opts):
        try:
            plan = build_plan(file)
            revisions = apply_plan(plan) if apply else []
        except ImportFileError as exc:
            raise CommandError(f"File rejected, nothing imported. {len(exc.errors)} error(s):\n"
                               + "\n".join(f"  - {e}" for e in exc.errors))
        for line in diff_lines(plan):
            self.stdout.write(line)
        out = Path(review_dir)
        out.mkdir(parents=True, exist_ok=True)
        review = out / f"{plan.brand.slug}-review.md"
        review.write_text(review_markdown(plan, applied=apply), encoding="utf-8")
        self.stdout.write("")
        if apply:
            self.stdout.write(self.style.SUCCESS(
                f"Saved {len(revisions)} draft revision(s), not published: "
                f"{', '.join(plan.changed_categories) or 'none'}. Review list: {review}"))
        else:
            self.stdout.write(self.style.WARNING(
                f"Dry run: nothing written to the site. Categories that would change: "
                f"{', '.join(plan.changed_categories) or 'none'}. Review list: {review}. Run again with --apply to save drafts."))
