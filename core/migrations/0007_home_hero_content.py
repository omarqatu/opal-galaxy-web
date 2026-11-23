"""Home page hero (approved premium composition): illustration, highlights, headline accent.

Additive, with the usual guards:
  * the two hero illustrations are added to the image library once (found again by title);
  * the three highlights are created only when the page has none;
  * the hero image is replaced only while it is still the villa photo placed in phase 2,
    and the mobile image is set only while it is empty;
  * the headline gets its accent markers only while it is still the approved text.
Other texts are not changed. The latest revision is patched with the live page.
A database with no home page is left alone. Reversing does nothing.
"""
import hashlib
from pathlib import Path

from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.db import migrations

# The hero image is a conceptual illustration, not a photograph of an Opal Galaxy installation.
IMAGES = {
    "desktop": ("hero-rooftop.jpg", "Home hero illustration (rooftop, wide)", 2000, 1125),
    "mobile": ("hero-rooftop-mobile.jpg", "Home hero illustration (rooftop, 4:3)", 1600, 1200),
}
PHASE2_HERO = "Gallery: Two inverter condensers beside a villa"
PHASE2_ALT = ("Two outdoor air-conditioning units installed beside a villa", "وحدتان خارجيتان للتكييف مركّبتان بجانب فيلا")
ALT = ("Illustration: a technician servicing rooftop air-conditioning units",
       "صورة توضيحية: فني يعمل على وحدات تكييف على سطح مبنى")
TITLES = {
    "hero_title_en": ("Engineered Cooling. Delivered with Confidence.",
                      "Engineered Cooling. *Delivered with Confidence.*"),
    "hero_title_ar": ("تكييف بمعايير هندسية، وتنفيذ جدير بالثقة", "تكييف بمعايير هندسية، *وتنفيذ جدير بالثقة*"),
}
HIGHLIGHTS = [
    ("supply", "HVAC supply and installation", "توريد أنظمة التكييف وتركيبها"),
    ("parts", "Maintenance and spare parts", "الصيانة وقطع الغيار"),
    ("project", "Project and contractor support", "دعم المشاريع والمقاولين"),
]


def add_image(apps, key):
    Image = apps.get_model("wagtailimages", "Image")
    Collection = apps.get_model("wagtailcore", "Collection")
    filename, title, width, height = IMAGES[key]
    existing = Image.objects.filter(title=title).first()
    if existing:
        return existing
    source = Path(settings.BASE_DIR) / "seed" / "images" / filename
    data = source.read_bytes()
    with source.open("rb") as fh:
        stored = default_storage.save(f"original_images/{filename}", File(fh))
    return Image.objects.create(title=title, file=stored, width=width, height=height, file_size=len(data),
                                file_hash=hashlib.sha1(data).hexdigest(),
                                collection=Collection.objects.order_by("depth", "path").first())


def apply_content(apps, schema_editor):
    HomePage = apps.get_model("core", "HomePage")
    home = HomePage.objects.first()
    if home is None:
        return
    Revision = apps.get_model("wagtailcore", "Revision")
    rev = Revision.objects.filter(pk=home.latest_revision_id).first() if home.latest_revision_id else None
    content = rev.content if rev else {}

    def put(field, old, new):
        if (getattr(home, field) or "") == old:
            setattr(home, field, new)
        if rev and (content.get(field) or "") == old:
            content[field] = new

    wide, mobile = add_image(apps, "desktop"), add_image(apps, "mobile")
    if home.hero_image_id and home.hero_image.title == PHASE2_HERO:
        home.hero_image = wide
        put("hero_alt_en", PHASE2_ALT[0], ALT[0])
        put("hero_alt_ar", PHASE2_ALT[1], ALT[1])
        if rev:
            content["hero_image"] = wide.pk
    if home.hero_image_mobile_id is None and home.hero_image_id == wide.pk:
        home.hero_image_mobile = mobile
        if rev:
            content["hero_image_mobile"] = mobile.pk
    for field, (old, new) in TITLES.items():
        put(field, old, new)
    home.save()

    HomeHighlight = apps.get_model("core", "HomeHighlight")
    if not HomeHighlight.objects.filter(page=home).exists():
        rows = [HomeHighlight.objects.create(page=home, sort_order=i, icon=icon, title_en=en, title_ar=ar)
                for i, (icon, en, ar) in enumerate(HIGHLIGHTS)]
        if rev and not content.get("highlights"):
            content["highlights"] = [{"pk": r.pk, "sort_order": r.sort_order, "page": home.pk, "icon": r.icon,
                                      "title_en": r.title_en, "title_ar": r.title_ar} for r in rows]
    if rev:
        rev.content = content
        rev.save()


class Migration(migrations.Migration):
    dependencies = [("core", "0006_home_hero_fields"), ("wagtailimages", "0027_image_description")]
    operations = [migrations.RunPython(apply_content, migrations.RunPython.noop)]
