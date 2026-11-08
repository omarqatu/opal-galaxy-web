"""Load a client's content from seed/<name>.json into an empty site.

Idempotent: does nothing if a HomePage already exists, unless --force is given
(--force replaces catalogue, home and service content; quote requests are kept).
"""
import json
from pathlib import Path

from django.conf import settings
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.images.models import Image
from wagtail.models import Page, Site

from catalog.models import Brand, KnowItem, ProductCategory, Supply
from core.models import (CompanySettings, ContractorPoint, FaqItem, GalleryItem, HomeFact, HomePage,
                         InstallStep, ServiceItem, ServicePage)


def bi(obj, field, value):
    value = value or {}
    setattr(obj, f"{field}_en", value.get("en", ""))
    setattr(obj, f"{field}_ar", value.get("ar", ""))


class Command(BaseCommand):
    help = "Seed the site from seed/<name>.json"

    def add_arguments(self, parser):
        parser.add_argument("--file", default=str(settings.BASE_DIR / "seed" / "opal.json"))
        parser.add_argument("--force", action="store_true")

    def image(self, name, title):
        if not name:
            return None
        existing = Image.objects.filter(title=title).first()
        if existing:
            return existing
        path = self.img_dir / name
        with path.open("rb") as fh:
            return Image.objects.create(title=title, file=ImageFile(fh, name=name))

    @transaction.atomic
    def handle(self, *args, **opts):
        path = Path(opts["file"])
        self.img_dir = path.parent / "images"
        if HomePage.objects.exists() and not opts["force"]:
            self.stdout.write("Site already seeded — skipping (use --force to reload).")
            return
        data = json.loads(path.read_text(encoding="utf-8"))

        # Company settings
        c = data["company"]
        cs = CompanySettings.load()
        for f in ("legal_name", "short_name", "phone", "phone_display", "whatsapp", "email", "address", "domain_label"):
            setattr(cs, f, c.get(f, ""))
        for f in ("tagline", "hours_short", "hours_full", "licence", "footer_about", "quote_reply"):
            bi(cs, f, c.get(f))
        cs.save()

        # Catalogue
        Supply.objects.all().delete(); KnowItem.objects.all().delete()
        ProductCategory.objects.all().delete(); Brand.objects.all().delete()
        brands = {}
        for i, b in enumerate(data["brands"]):
            obj = Brand(slug=b["slug"], name=b["name"], sort_order=i)
            for f in ("origin", "line", "about"):
                bi(obj, f, b.get(f))
            obj.save(); brands[b["slug"]] = obj
        for i, cat in enumerate(data["categories"]):
            obj = ProductCategory(slug=cat["slug"], capacity_range=cat.get("range", ""), sort_order=i,
                                  icon=cat.get("icon") or "",
                                  image=self.image(cat.get("image"), f"Product: {cat['name']['en']}"))
            bi(obj, "name", cat["name"]); bi(obj, "lead", cat.get("lead"))
            obj.save()
            for j, k in enumerate(cat.get("know", [])):
                ki = KnowItem(category=obj, sort_order=j); bi(ki, "title", k["title"]); bi(ki, "text", k["text"]); ki.save()
            for j, s in enumerate(cat.get("supply", [])):
                Supply.objects.create(category=obj, brand=brands[s["brand"]], sort_order=j,
                                      models_text=s["models"], specs="\n".join(s.get("specs", [])),
                                      pending=bool(s.get("pending")))

        # Pages: replace the default Wagtail welcome page with our home page
        root = Page.get_first_root_node()
        for old in HomePage.objects.all():
            old.delete()
        h = data["home"]
        home = HomePage(title=data["company"]["short_name"].title(), slug="home")
        for f in ("seo_title", "meta_description", "hero_title", "hero_lead", "hero_alt", "hero_caption",
                  "hero_subcaption", "products_title", "products_lead", "brands_title", "brands_lead",
                  "contractors_title", "contractors_lead", "install_title", "install_lead", "install_link",
                  "projects_title", "projects_lead", "about_title", "about_text", "faq_title", "faq_lead"):
            bi(home, f, h.get(f))
        home.hero_image = self.image(h.get("hero_image"), "Home hero")
        for j, x in enumerate(h.get("facts", [])):
            o = HomeFact(sort_order=j); bi(o, "title", x["title"]); bi(o, "text", x["text"]); home.facts.add(o)
        for j, x in enumerate(h.get("contractor_points", [])):
            o = ContractorPoint(sort_order=j); bi(o, "title", x["title"]); bi(o, "text", x["text"]); home.contractor_points.add(o)
        for j, x in enumerate(h.get("install_steps", [])):
            o = InstallStep(sort_order=j); bi(o, "title", x["title"]); bi(o, "text", x["text"]); home.install_steps.add(o)
        for j, x in enumerate(h.get("gallery", [])):
            o = GalleryItem(sort_order=j, image=self.image(x["image"], f"Gallery: {x['alt']['en']}"))
            for f in ("alt", "caption", "subcaption"):
                bi(o, f, x.get(f))
            home.gallery.add(o)
        for j, x in enumerate(h.get("faqs", [])):
            o = FaqItem(sort_order=j); bi(o, "question", x["q"]); bi(o, "answer", x["a"]); home.faqs.add(o)
        # Wagtail's default welcome page also uses slug "home": remove plain Page leftovers first.
        site = Site.objects.filter(is_default_site=True).first()
        for p in Page.objects.filter(depth=2).specific():
            if type(p) is Page:
                if site and site.root_page_id == p.pk:
                    site.root_page = root; site.save()
                p.delete()
        root = Page.objects.get(pk=root.pk)  # refresh treebeard's child count after deletes
        root.add_child(instance=home)
        home.save_revision().publish()

        for s in data.get("services", []):
            sp = ServicePage(title=s["title"]["en"], slug=s["slug"])
            for f in ("title", "lead", "cta", "list_title"):
                bi(sp, f, s.get(f))
            for j, x in enumerate(s.get("items", [])):
                o = ServiceItem(sort_order=j); bi(o, "title", x["title"]); bi(o, "text", x["text"]); sp.items.add(o)
            home.add_child(instance=sp)
            sp.save_revision().publish()

        site = Site.objects.filter(is_default_site=True).first()
        if site:
            site.root_page = home; site.site_name = data["company"]["legal_name"]; site.save()
        else:
            Site.objects.create(hostname="localhost", port=80, root_page=home, is_default_site=True,
                                site_name=data["company"]["legal_name"])
        self.stdout.write(self.style.SUCCESS(
            f"Seeded: {Brand.objects.count()} brands, {ProductCategory.objects.count()} categories, "
            f"{Supply.objects.count()} matrix cells, {Image.objects.count()} images."))
