# Field gallery: transition from the home page gallery to standalone field photos

Decision (Omar, 23 Nov 2026): the gallery moves to a native Wagtail model, `FieldPhoto`, with its own admin area, bulk upload, filters and pagination. The inline "Gallery photos" editor on the home page is retired once the replacement is complete and verified.

## Where things stand

| Step | Content | State |
|---|---|---|
| PR 1 | `FieldPhoto` model, Field gallery admin area (listing, filters, search, pagination), approval permission, guarded mirror of the existing rows | this PR |
| PR 2 | Bulk upload into the "Field gallery" image collection, bulk actions (approve, withdraw, category, homepage), paginated public gallery (24 per page), **the switch** | not started |
| PR 3 | Removal of `GalleryItem` and its table | only after Omar's explicit approval |

## How the existing gallery keeps working

Until the switch in PR 2, nothing a visitor sees depends on the new table.

- The home page and the gallery page read `GalleryItem`, exactly as before.
- Photos are still added, ordered and approved under Pages → Home → Gallery photos.
- Field gallery → Photos shows mirrors of those rows. It is there for review. **Edits made there to a mirrored photo are overwritten by the next mirror run**, because the old editor is still the source of truth.

## The mirror

`core/gallery.py: sync_field_photos()` copies every `GalleryItem` into `FieldPhoto`.

| Old field | New field |
|---|---|
| image (same Wagtail image record) | image |
| alt_en / alt_ar | alt_en / alt_ar |
| caption_en / caption_ar | title_en / title_ar |
| subcaption_en / subcaption_ar | caption_en / caption_ar |
| category, featured, approved_for_publication | same names |
| sort_order | sort_order (manual order) |
| first eight approved rows, in order | show_on_homepage, home_order 1–8 |
| row id | legacy_item_id (unique) |

Guarantees, all covered by tests:

- **No duplicates.** A row is matched by `legacy_item_id`, which is unique in the database. Running the step again creates nothing new.
- **No file is copied.** The photo points at the same image record.
- **Nothing is deleted.** A row removed from the old gallery leaves its mirror in place, unapproved and off the home page.
- **`GalleryItem`, images and files are never written to.**
- Photos created in the new area (no `legacy_item_id`) are never touched.

It runs in three places: migration `core 0010` (applied automatically by `entrypoint.sh` on start), `seed_site` on an empty database, and the command below.

## Commands

```bash
python manage.py sync_field_photos --check
```
Prints the row counts of both tables and fails if any row differs.

```bash
python manage.py sync_field_photos --dry-run
```
Reports what a run would create or update and writes nothing.

```bash
python manage.py sync_field_photos
```
Brings the mirrors up to date.

## The switch (PR 2)

1. Final mirror run in a migration, then a count and row check.
2. Home page and gallery page read `FieldPhoto` (approved photos; home page: up to eight with "Show on homepage").
3. The "Gallery photos" panel leaves the home page editor. `GalleryItem` rows stay in the database, unused.
4. From that point the mirror is disabled, so the new area becomes the only place photos are managed.

## Rollback and recovery

- **PR 1:** the site does not read the new table. Deploying the previous image restores the previous state; the extra table is ignored by the older code. `python manage.py migrate core 0009` removes the table if wanted. No gallery data can be lost because none is modified.
- **After the switch:** the `GalleryItem` rows are still present and complete, so deploying the pre-switch image brings the old editor and pages back with the data as it was at the switch. Photos added in the new area after the switch exist only in `FieldPhoto` and stay there for the next attempt.
- **Database:** the regular backup taken before each deploy remains the last resort.
- The old table is dropped only in PR 3, after Omar's explicit approval.
