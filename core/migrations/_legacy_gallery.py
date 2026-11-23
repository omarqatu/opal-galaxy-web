"""Support code for migrations 0010 and 0011 only (the file name starts with "_" so Django does not load it as a migration).

It copied the rows of the former home page gallery (GalleryItem) into FieldPhoto. GalleryItem was
removed in 0012; nothing outside these two migrations uses this module.
"""
HOME_LIMIT = 8


def mirror_values(item, home_position):
    return {
        "image_id": item.image_id,
        "alt_en": item.alt_en, "alt_ar": item.alt_ar,
        "title_en": item.caption_en, "title_ar": item.caption_ar,
        "caption_en": item.subcaption_en, "caption_ar": item.subcaption_ar,
        "category_id": item.category_id,
        "featured": item.featured,
        "approved_for_publication": item.approved_for_publication,
        "sort_order": item.sort_order,
        "show_on_homepage": home_position is not None,
        "home_order": home_position or 0,
    }


def sync_field_photos(GalleryItem, FieldPhoto, dry_run=False, update_existing=False):
    """Copy GalleryItem rows into FieldPhoto. Safe to run any number of times.

    Field photos are now what the site shows and what Omar edits, so by default only rows that have
    no field photo yet are created; existing photos are never overwritten or withdrawn. The final
    run of the switch (core 0011) passed update_existing=True once, while GalleryItem still led.

    The model classes are passed in so the same code serves the migration (historical models),
    the management command and the tests. Returns a report of what was, or would be, done.
    """
    items = list(GalleryItem.objects.order_by("sort_order", "pk"))
    existing = {p.legacy_item_id: p for p in FieldPhoto.objects.exclude(legacy_item_id=None)}
    report = {"items": len(items), "created": 0, "updated": 0, "unchanged": 0, "withdrawn": 0}
    on_home = 0
    for item in items:
        position = None
        if item.approved_for_publication and on_home < HOME_LIMIT:   # what the home page shows today
            on_home += 1
            position = on_home
        values = mirror_values(item, position)
        photo = existing.get(item.pk)
        if photo is None:
            report["created"] += 1
            if not dry_run:
                FieldPhoto.objects.create(legacy_item_id=item.pk, **values)
        elif update_existing and any(getattr(photo, k) != v for k, v in values.items()):
            report["updated"] += 1
            if not dry_run:
                FieldPhoto.objects.filter(pk=photo.pk).update(**values)
        else:
            report["unchanged"] += 1
    # A row removed from the home page gallery must not stay public through its mirror. The mirror is kept.
    gone = [p for legacy_id, p in existing.items() if update_existing and legacy_id not in {i.pk for i in items}
            and (p.approved_for_publication or p.show_on_homepage)]
    report["withdrawn"] = len(gone)
    if gone and not dry_run:
        FieldPhoto.objects.filter(pk__in=[p.pk for p in gone]).update(approved_for_publication=False, show_on_homepage=False)
    report["mirrors"] = len(existing) + (0 if dry_run else report["created"])
    return report


def verify(GalleryItem, FieldPhoto):
    """Compare both tables row by row. Returns a list of differences; empty means they agree."""
    problems = []
    photos = {p.legacy_item_id: p for p in FieldPhoto.objects.exclude(legacy_item_id=None)}
    on_home = 0
    for item in GalleryItem.objects.order_by("sort_order", "pk"):
        position = None
        if item.approved_for_publication and on_home < HOME_LIMIT:
            on_home += 1
            position = on_home
        photo = photos.get(item.pk)
        if photo is None:
            problems.append(f"gallery row {item.pk} has no field photo")
            continue
        for key, value in mirror_values(item, position).items():
            if getattr(photo, key) != value:
                problems.append(f"gallery row {item.pk}: {key} differs")
    return problems
