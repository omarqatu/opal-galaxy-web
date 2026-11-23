"""The switch: field photos become what the site shows and what is edited in the admin.

One last copy from the home page gallery, this time also bringing already copied photos up to date,
because until this moment the old editor was still in use. From here on the copy only ever creates
missing rows and never overwrites a field photo. GalleryItem rows, images and files are not changed
or removed. No schema change. Reversing does nothing.
"""
from django.db import migrations

from . import _legacy_gallery as gallery


def final_copy(apps, schema_editor):
    GalleryItem, FieldPhoto = apps.get_model("core", "GalleryItem"), apps.get_model("core", "FieldPhoto")
    gallery.sync_field_photos(GalleryItem, FieldPhoto, update_existing=True)
    problems = gallery.verify(GalleryItem, FieldPhoto)
    if problems:   # stop the deploy rather than switch with differing data
        raise RuntimeError("field photos do not match the gallery rows: " + "; ".join(problems))


class Migration(migrations.Migration):
    dependencies = [("core", "0010_field_photos")]
    operations = [migrations.RunPython(final_copy, migrations.RunPython.noop)]
