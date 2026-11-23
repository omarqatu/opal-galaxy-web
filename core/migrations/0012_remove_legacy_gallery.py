"""Retire the former home page gallery (GalleryItem). Approved by Omar on 23 Nov 2026.

Field photos have been the live gallery since 0011, which copied every row and refused to continue
unless both tables agreed. Before the table is dropped, each remaining row is written to a JSON file
under DATA_DIR/archive (the persistent volume), together with the id of its field photo, so the
texts can be read back without a database restore. If that file cannot be written the migration
stops and nothing is dropped.

Dropped: table core_galleryitem. Not touched: field photos, gallery categories, images, image files.
Reversing recreates the empty table; the archive file is the source for refilling it.
"""
import json
from pathlib import Path

from django.conf import settings
from django.db import migrations, models
from django.utils import timezone

FIELDS = ("id", "page_id", "image_id", "sort_order", "alt_en", "alt_ar", "caption_en", "caption_ar",
          "subcaption_en", "subcaption_ar", "category_id", "featured", "approved_for_publication")


def archive_rows(apps, schema_editor):
    GalleryItem = apps.get_model("core", "GalleryItem")
    FieldPhoto = apps.get_model("core", "FieldPhoto")
    rows = list(GalleryItem.objects.order_by("sort_order", "pk").values(*FIELDS))
    if not rows:
        return
    photos = dict(FieldPhoto.objects.exclude(legacy_item_id=None).values_list("legacy_item_id", "pk"))
    for row in rows:
        row["field_photo_id"] = photos.get(row["id"])
    folder = Path(settings.DATA_DIR) / "archive"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"legacy-gallery-items-{timezone.now():%Y%m%d-%H%M%S}.json"
    target.write_text(json.dumps({"table": "core_galleryitem", "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    if len(json.loads(target.read_text(encoding="utf-8"))["rows"]) != len(rows):
        raise RuntimeError("the archive of the legacy gallery rows could not be verified; nothing was dropped")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_field_photos_switch"),
    ]

    operations = [
        migrations.RunPython(archive_rows, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="fieldphoto",
            name="legacy_item_id",
            field=models.PositiveIntegerField(
                blank=True,
                editable=False,
                help_text="The id this photo had in the former home page gallery, if any",
                null=True,
                unique=True,
            ),
        ),
        migrations.DeleteModel(
            name="GalleryItem",
        ),
    ]
