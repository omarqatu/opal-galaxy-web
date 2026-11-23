"""Gallery: put the two strongest job photos first (they lead the gallery layout).

Only the order changes, and only while the gallery is still in its original order; a gallery
the operator has reordered, extended or trimmed is left as it is. Captions and images are
not touched. The latest revision is patched with the live rows. Reversing does nothing.
"""
from django.db import migrations

ORIGINAL = [
    "Gallery: Rooftop package units on a commercial building",
    "Gallery: Two inverter condensers beside a villa",
    "Gallery: Crane lifting a package unit onto a roof",
    "Gallery: Package unit at a warehouse",
    "Gallery: Ducted unit delivered to a villa site",
    "Gallery: Technician vacuuming a split system",
    "Gallery: Floors and furniture covered during installation",
    "Gallery: Batch of boxed units on a residential site",
]
LEAD = [ORIGINAL[1], ORIGINAL[2]]


def apply_content(apps, schema_editor):
    HomePage = apps.get_model("core", "HomePage")
    home = HomePage.objects.first()
    if home is None:
        return
    GalleryItem = apps.get_model("core", "GalleryItem")
    items = list(GalleryItem.objects.filter(page=home).select_related("image").order_by("sort_order", "pk"))
    if [i.image.title for i in items] != ORIGINAL:
        return
    ordered = [i for t in LEAD for i in items if i.image.title == t] + [i for i in items if i.image.title not in LEAD]
    new_order = {}
    for position, item in enumerate(ordered):
        new_order[item.pk] = position
        if item.sort_order != position:
            item.sort_order = position
            item.save(update_fields=["sort_order"])
    Revision = apps.get_model("wagtailcore", "Revision")
    rev = Revision.objects.filter(pk=home.latest_revision_id).first() if home.latest_revision_id else None
    if rev and sorted(i.get("pk") for i in rev.content.get("gallery", [])) == sorted(new_order):
        for entry in rev.content["gallery"]:
            entry["sort_order"] = new_order[entry["pk"]]
        rev.content["gallery"].sort(key=lambda e: e["sort_order"])
        rev.save(update_fields=["content"])


class Migration(migrations.Migration):
    dependencies = [("core", "0007_home_hero_content")]
    operations = [migrations.RunPython(apply_content, migrations.RunPython.noop)]
