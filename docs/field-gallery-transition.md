# Field gallery

The gallery is a native Wagtail feature built on one model, `FieldPhoto`, managed under **Field gallery** in the admin. The former home page gallery (`GalleryItem`) was copied into it and then removed.

| Step | Content | State |
|---|---|---|
| PR 1 (#19) | `FieldPhoto` model, admin area, approval permission, first copy of the old rows | merged |
| PR 2 (#20) | Bulk upload, bulk actions, paginated public gallery, the switch (`core 0011`: final copy, then a row-by-row check that stops the deploy on any difference) | merged |
| PR 3 | Removal of `GalleryItem`, its table and the transition code (`core 0012`) | this PR |

## How it works

- A photo is public only when "Approved for publication" is ticked.
- Home page: up to eight approved photos with "Show on homepage", lowest "Homepage order" first.
- Gallery page: photos with a manual number first (lowest first), then the rest newest first; 24 per page; category filter.
- The image file exists once, in Wagtail Images. A photo record cannot lose its image: an image in use cannot be deleted.

### Adding photos

1. Field gallery → Upload photos. Wagtail's multi-file uploader opens with the "Field gallery" collection selected.
2. Drop or choose any number of files. Each becomes one image and one field photo, unapproved, not featured, not on the home page.
3. Field gallery → Photos, filter "Approved for publication: no". Open a photo to add alt text, title, caption and category, or tick several and use the bar at the bottom: Approve, Withdraw approval, Show on home, Remove from home, Set category.

Upload rules are Wagtail's: AVIF, GIF, JPG, PNG and WEBP, 10 MB per file, a pixel-count limit, duplicate detection. Keep the collection on "Field gallery"; an image uploaded elsewhere is an ordinary library image and gets no field photo.

### Permissions

| Action | Needs |
|---|---|
| Upload | add field photo + add image |
| Edit, set category, homepage on / off (single or bulk) | change field photo |
| Approve, withdraw approval (single or bulk) | `approve_fieldphoto` |

Superusers have all of them. No group is given `approve_fieldphoto` automatically.

## What PR 3 removed

| Kind | Removed |
|---|---|
| Database table | `core_galleryitem` |
| Model | `core.GalleryItem` (and with it the `HomePage.gallery` relation) |
| Management command | `sync_field_photos` |
| Module | `core/gallery.py`, moved to `core/migrations/_legacy_gallery.py`: migrations 0010 and 0011 still need it to run on an empty database; nothing else imports it |
| Seed | `seed_site` creates field photos directly; `seed/opal.json` lists the photos in their final order and carries the one Arabic caption correction that migrations 0005 and 0008 used to apply to the old rows |

Kept: every `FieldPhoto` and `GalleryCategory` record, every Wagtail image record and file, and `FieldPhoto.legacy_item_id` (the id a photo had in the old gallery).

Old home page revisions still contain the former gallery rows inside their stored JSON. Wagtail ignores them (tested); they are not removed.

## Archive written by `core 0012`

Before dropping the table, the migration writes every remaining row to

```
<DATA_DIR>/archive/legacy-gallery-items-<UTC date-time>.json
```

`DATA_DIR` is `/app/data` in the container, the persistent volume that is backed up daily with the images. Each row holds all thirteen columns plus `field_photo_id`, the photo it became (empty if that photo was deleted in the new area since). If the file cannot be written and read back, the migration stops and the table is not dropped. On a database with no old rows no file is written.

## Recovery

| Situation | What to do |
|---|---|
| A text or setting of an old photo is needed | Read it from the archive file; nothing has to be restored. |
| The deploy stops in `core 0012` | Nothing was dropped (the migration runs in one transaction). The previous container image still works with the database as it is. |
| Field photos are damaged after the deploy | Restore the daily database backup taken before the deploy (S3, bucket `omardigital`, database `opalDB`). Image files are not affected by this PR. |
| The old table itself is wanted back | `python manage.py migrate core 0011` recreates it empty; its rows can be re-entered from the archive file. The site no longer reads it. |

Rolling back to the image of PR 2 after `0012` has run is **not** a working state: that code expects the table. Use the database backup together with the older image, or stay on the current one.

**Before deploying PR 3:** confirm that last night's backup of `opalDB` succeeded (the confirmation email), or take a manual backup. The roadmap still lists a test restore as not done; the archive file exists so that this removal does not depend on one.
