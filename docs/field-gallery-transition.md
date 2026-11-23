# Field gallery: transition from the home page gallery to standalone field photos

Decision (Omar, 23 Nov 2026): the gallery moves to a native Wagtail model, `FieldPhoto`, with its own admin area, bulk upload, filters and pagination. The inline "Gallery photos" editor on the home page is retired once the replacement is complete and verified.

## Where things stand

| Step | Content | State |
|---|---|---|
| PR 1 | `FieldPhoto` model, Field gallery admin area, approval permission, guarded copy of the existing rows | merged |
| PR 2 | Bulk upload, bulk actions, paginated public gallery (24 per page), **the switch** | this PR |
| PR 3 | Removal of `GalleryItem` and its table | only after Omar's explicit approval |

## How the gallery works after PR 2

- The home page and the gallery page read `FieldPhoto`. A photo is public only when "Approved for publication" is ticked.
- The home page shows up to eight approved photos that have "Show on homepage", lowest "Homepage order" first.
- The gallery lists manual numbers first (lowest first), then the rest newest first, 24 per page.
- Photos are managed only under **Field gallery** in the admin. The "Gallery photos" panel is gone from the home page editor.
- `GalleryItem` rows remain in the database, complete and unused.

### Adding photos

1. Field gallery → Upload photos. This opens Wagtail's multi-file uploader with the "Field gallery" collection selected (the collection is created on first use).
2. Drop or choose any number of files. Each becomes one image and one field photo, unapproved, not featured, not on the home page.
3. Field gallery → Photos, filter "Approved for publication: no". Open a photo to add alt text, title and caption in both languages and the category; or tick several and use the bar at the bottom: Approve, Withdraw approval, Show on home, Remove from home, Set category.

Upload rules are Wagtail's: AVIF, GIF, JPG, PNG and WEBP, 10 MB per file, a pixel-count limit, duplicate detection. Leave the collection on "Field gallery"; an image uploaded to another collection is an ordinary library image and gets no field photo.

### Permissions

| Action | Needs |
|---|---|
| Upload | add field photo + add image |
| Edit, set category, homepage on / off (single or bulk) | change field photo |
| Approve, withdraw approval (single or bulk) | `approve_fieldphoto` |

Superusers have all of them. No group is given `approve_fieldphoto` automatically.

## The copy from the old gallery

`core/gallery.py: sync_field_photos()` copies `GalleryItem` rows into `FieldPhoto`. Migration `core 0011` ran it one last time in full (creating missing photos and bringing existing ones up to date) and stops the deploy if the two tables then differ. Since then it only creates a photo for a row that has none and never overwrites or withdraws a photo.

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

## Rollback and recovery

- **Back to the previous image:** the `GalleryItem` rows are untouched, so the previous image shows the old gallery and the old editor exactly as they were at the switch. `FieldPhoto` rows stay in their table, ignored by the older code, and are picked up again on the next deploy of this version.
- **Photos uploaded after the switch** exist only as images and field photos. They survive a rollback (the table is not dropped) but are not shown by the older code.
- **If `core 0011` stops the deploy** with "field photos do not match the gallery rows", nothing has been switched in the database: the migration is rolled back and `entrypoint.sh` stops, so the new container does not start. The message names the differing rows. Redeploy the previous image while the difference is looked at.
- **Database:** the regular backup taken before each deploy remains the last resort.
- The old table is dropped only in PR 3, after Omar's explicit approval.
