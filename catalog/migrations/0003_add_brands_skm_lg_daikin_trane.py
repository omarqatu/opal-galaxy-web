"""Add the brand records SKM, LG, Daikin and Trane (name only).

Their texts, series and logos are written by the site operator in the admin, so this
migration creates the records and nothing else. A brand whose slug already exists is
left exactly as it is. Reversing the migration does nothing: brands are never deleted
by a migration.
"""
from django.db import migrations

NEW_BRANDS = [("skm", "SKM"), ("lg", "LG"), ("daikin", "Daikin"), ("trane", "Trane")]


def add_brands(apps, schema_editor):
    Brand = apps.get_model("catalog", "Brand")
    if not Brand.objects.exists():
        return  # empty database: seed_site creates every brand from seed/opal.json
    order = max(Brand.objects.values_list("sort_order", flat=True))
    for slug, name in NEW_BRANDS:
        if Brand.objects.filter(slug=slug).exists():
            continue
        order += 1
        Brand.objects.create(slug=slug, name=name, sort_order=order)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0002_remove_origin_add_source_drafts")]
    operations = [migrations.RunPython(add_brands, migrations.RunPython.noop)]
