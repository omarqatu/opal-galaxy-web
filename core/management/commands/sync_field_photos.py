from django.core.management.base import BaseCommand, CommandError

from core import gallery
from core.models import FieldPhoto, GalleryItem


class Command(BaseCommand):
    help = ("Create a field photo for any home page gallery row that has none. Field photos are the live "
            "gallery now, so existing photos are never overwritten. Safe to repeat; never duplicates or deletes.")

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report what would change and write nothing")
        parser.add_argument("--check", action="store_true", help="Compare the two tables (meaningful only until photos are edited in the new area)")

    def handle(self, *args, **opts):
        if opts["check"]:
            problems = gallery.verify(GalleryItem, FieldPhoto)
            self.stdout.write(f"gallery rows: {GalleryItem.objects.count()}, "
                              f"mirrored field photos: {FieldPhoto.objects.exclude(legacy_item_id=None).count()}, "
                              f"field photos in total: {FieldPhoto.objects.count()}")
            if problems:
                raise CommandError("; ".join(problems))
            self.stdout.write("The two tables agree.")
            return
        r = gallery.sync_field_photos(GalleryItem, FieldPhoto, dry_run=opts["dry_run"])
        self.stdout.write(("Dry run. " if opts["dry_run"] else "") +
                          f"gallery rows: {r['items']}; created {r['created']}, updated {r['updated']}, "
                          f"unchanged {r['unchanged']}, withdrawn {r['withdrawn']}")
