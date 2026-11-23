"""Standalone field photos (FieldPhoto), the future replacement of the home page's inline gallery.

The new table is created and every existing gallery row is mirrored into it: same image record (no
file is copied), same texts, category, approval and order. The step can run any number of times and
never creates a second copy of a row. GalleryItem, images and files are not changed; the public site
keeps reading GalleryItem until the switch. Reversing drops only the new table.
"""
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

from core import gallery


def mirror(apps, schema_editor):
    gallery.sync_field_photos(apps.get_model("core", "GalleryItem"), apps.get_model("core", "FieldPhoto"))


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_gallery_categories_and_approval"),
        ("wagtailimages", "0027_image_description"),
    ]

    operations = [
        migrations.CreateModel(
            name="FieldPhoto",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "alt_en",
                    models.CharField(
                        blank=True,
                        help_text="What the photo shows, for screen readers and search engines",
                        max_length=200,
                        verbose_name="Alt text (EN)",
                    ),
                ),
                (
                    "alt_ar",
                    models.CharField(
                        blank=True, max_length=200, verbose_name="Alt text (AR)"
                    ),
                ),
                (
                    "title_en",
                    models.CharField(
                        blank=True, max_length=120, verbose_name="Title (EN)"
                    ),
                ),
                (
                    "title_ar",
                    models.CharField(
                        blank=True, max_length=120, verbose_name="Title (AR)"
                    ),
                ),
                (
                    "caption_en",
                    models.CharField(
                        blank=True, max_length=200, verbose_name="Caption (EN)"
                    ),
                ),
                (
                    "caption_ar",
                    models.CharField(
                        blank=True, max_length=200, verbose_name="Caption (AR)"
                    ),
                ),
                (
                    "approved_for_publication",
                    models.BooleanField(
                        default=False,
                        help_text="The photo appears on the site only when this is ticked. Tick it after checking that the photo shows no identifiable face or vehicle number plate, or that permission was given or the photo was redacted.",
                        verbose_name="Approved for publication",
                    ),
                ),
                (
                    "featured",
                    models.BooleanField(
                        default=False,
                        help_text="Shown larger in the gallery. Only the first two featured photos lead.",
                        verbose_name="Featured photo",
                    ),
                ),
                (
                    "show_on_homepage",
                    models.BooleanField(
                        default=False,
                        help_text="The home page shows up to eight approved photos that have this ticked.",
                        verbose_name="Show on homepage",
                    ),
                ),
                (
                    "home_order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Lower numbers come first on the home page",
                        verbose_name="Homepage order",
                    ),
                ),
                (
                    "sort_order",
                    models.IntegerField(
                        blank=True,
                        help_text="Optional. Photos with a number come first, lowest first; the rest follow, newest first.",
                        null=True,
                        verbose_name="Manual order",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False
                    ),
                ),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "legacy_item_id",
                    models.PositiveIntegerField(
                        blank=True,
                        editable=False,
                        help_text="The home page gallery row this photo was imported from, if any",
                        null=True,
                        unique=True,
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="field_photos",
                        to="core.gallerycategory",
                    ),
                ),
                (
                    "image",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="wagtailimages.image",
                    ),
                ),
            ],
            options={
                "verbose_name": "Field photo",
                "verbose_name_plural": "Field photos",
                "ordering": [
                    models.OrderBy(models.F("sort_order"), nulls_last=True),
                    "-created",
                    "-pk",
                ],
                "permissions": [
                    ("approve_fieldphoto", "Can approve field photos for publication")
                ],
            },
        ),
        migrations.RunPython(mirror, migrations.RunPython.noop),
    ]
