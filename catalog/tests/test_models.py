from decimal import Decimal

from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase

from catalog.models import Brand, ProductCategory, Supply

def shown_text(response):
    """The page as a reader gets it: tags removed, whitespace collapsed."""
    import html
    import re
    markup = re.sub(r"</?(?:span|b|i)\b[^>]*>", "", response.content.decode())   # inline wrappers add no space
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", markup)))


def model_pieces(models_text):
    """The pieces of a stored models string as the panels lay them out (cut at " · " and after "Label:")."""
    import re
    out = []
    for part in re.split(r" · |\.\s+(?=[A-Z][\\w &/()\\-]{1,40}:\s)", models_text):
        out.extend(x.strip() for x in re.split(r"(?<=:)\s", part, maxsplit=1) if x.strip())
    return out



class MigrationKeepsContentTests(TransactionTestCase):
    """0002 must not change any visible catalogue content (only the brand origin goes)."""

    before = [("catalog", "0001_initial")]
    after = [("catalog", "0002_remove_origin_add_source_drafts")]

    def migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def tearDown(self):
        self.migrate(executor_leaf())

    def test_existing_rows_survive_unchanged(self):
        old = self.migrate(self.before)
        OBrand = old.get_model("catalog", "Brand")
        OCat = old.get_model("catalog", "ProductCategory")
        OSupply = old.get_model("catalog", "Supply")
        b = OBrand.objects.create(slug="acme", name="Acme", origin_en="Japan", origin_ar="اليابان",
                                  line_en="Line", line_ar="سطر", about_en="About", about_ar="نبذة")
        c = OCat.objects.create(slug="wall", name_en="Wall", name_ar="جداري", capacity_range="9,000 – 36,000 BTU",
                                lead_en="Lead", lead_ar="مقدمة")
        OSupply.objects.create(category=c, brand=b, sort_order=3, models_text="X 12 · X 18",
                               specs="R410A\n1.5 – 3 ton", pending=False)
        OSupply.objects.create(category=c, brand=OBrand.objects.create(slug="b2", name="B2"),
                               models_text="Y", specs="", pending=True)

        new = self.migrate(self.after)
        NBrand = new.get_model("catalog", "Brand")
        NCat = new.get_model("catalog", "ProductCategory")
        NSupply = new.get_model("catalog", "Supply")

        b = NBrand.objects.get(slug="acme")
        self.assertEqual((b.name, b.line_en, b.line_ar, b.about_en, b.about_ar),
                         ("Acme", "Line", "سطر", "About", "نبذة"))
        self.assertFalse(hasattr(b, "origin_en"))
        c = NCat.objects.get(slug="wall")
        self.assertEqual((c.name_en, c.name_ar, c.capacity_range, c.lead_en, c.lead_ar),
                         ("Wall", "جداري", "9,000 – 36,000 BTU", "Lead", "مقدمة"))
        self.assertTrue(c.live)
        self.assertFalse(c.has_unpublished_changes)
        self.assertIsNone(c.latest_revision_id)
        rows = {s.brand.slug: s for s in NSupply.objects.select_related("brand")}
        s = rows["acme"]
        self.assertEqual((s.models_text, s.specs, s.pending, s.sort_order),
                         ("X 12 · X 18", "R410A\n1.5 – 3 ton", False, 3))
        self.assertEqual(rows["b2"].pending, True)
        for s in rows.values():
            self.assertEqual(s.source_type, "unknown")
            self.assertEqual(s.source, "")
            self.assertIsNone(s.nominal_tons_min)
            self.assertIsNone(s.nominal_tons_max)


def executor_leaf():
    executor = MigrationExecutor(connection)
    return executor.loader.graph.leaf_nodes()


class PublicSiteShowsOnlyPublishedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)
        cls.carrier = Brand.objects.get(slug="carrier")
        cls.sg = Brand.objects.get(slug="super-general")
        # A category that only exists as a draft (never published)
        cls.draft_cat = ProductCategory(slug="draft-only", name_en="Secret draft type", name_ar="مسودة سرية")
        cls.draft_cat.live = False
        cls.draft_cat.save()
        Supply.objects.create(category=cls.draft_cat, brand=cls.carrier, models_text="DRAFTMODEL-1")
        # A published category with unpublished changes
        cls.window = ProductCategory.objects.get(slug="window")
        rows = list(cls.window.supplies.all())
        row = next(r for r in rows if r.brand_id == cls.sg.pk)
        cls.published_models = row.models_text
        row.models_text = "UNPUBLISHED-CHANGE-42"
        cls.window.supplies = rows
        cls.window.save_revision()  # draft only; the live row is untouched

    def test_draft_only_category_is_hidden_everywhere(self):
        self.assertEqual(self.client.get("/products/draft-only/").status_code, 404)
        self.assertEqual(self.client.get("/ar/products/draft-only/").status_code, 404)
        for path in ("/", "/ar/", "/products/wall/", "/brands/carrier/", "/ar/brands/carrier/", "/maintenance/"):
            with self.subTest(path=path):
                r = self.client.get(path)
                self.assertEqual(r.status_code, 200)
                self.assertNotContains(r, "Secret draft type")
                self.assertNotContains(r, "مسودة سرية")
                self.assertNotContains(r, "draft-only")
                self.assertNotContains(r, "DRAFTMODEL-1")
        self.assertNotContains(self.client.get("/sitemap.xml"), "draft-only")
        self.assertNotIn(self.draft_cat, self.carrier.categories())

    def test_unpublished_changes_stay_off_the_site(self):
        self.window.refresh_from_db()
        self.assertTrue(self.window.has_unpublished_changes)
        for path in ("/products/window/", "/brands/super-general/"):
            with self.subTest(path=path):
                r = self.client.get(path)
                text = shown_text(r)
                for piece in model_pieces(self.published_models):
                    self.assertIn(piece, text)
                self.assertNotContains(r, "UNPUBLISHED-CHANGE-42")

    def test_publishing_the_revision_makes_it_public(self):
        self.window.refresh_from_db()
        self.window.latest_revision.publish()
        self.assertContains(self.client.get("/products/window/"), "UNPUBLISHED-CHANGE-42")

    def test_draft_preview_uses_public_template_in_both_languages(self):
        draft = self.window.latest_revision.as_object()
        en = draft.make_preview_request(preview_mode="en")
        self.assertEqual(en.status_code, 200)
        self.assertContains(en, "UNPUBLISHED-CHANGE-42")
        self.assertContains(en, '<html lang="en"')
        ar = draft.make_preview_request(preview_mode="ar")
        self.assertContains(ar, "UNPUBLISHED-CHANGE-42")
        self.assertContains(ar, 'dir="rtl"')
        self.assertContains(ar, "وحدات شباك")


class SupplyFieldsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def test_seeded_rows_default_to_unknown_source(self):
        self.assertEqual(Supply.objects.exclude(source_type="unknown").count(), 0)

    def test_tons_keep_exact_decimal(self):
        s = Supply.objects.first()
        s.nominal_tons_min, s.nominal_tons_max = Decimal("1.5"), Decimal("2")
        s.save()
        s.refresh_from_db()
        self.assertEqual((s.nominal_tons_min, s.nominal_tons_max), (Decimal("1.5"), Decimal("2")))

    def test_brand_pages_do_not_show_origin(self):
        for path in ("/brands/carrier/", "/ar/brands/carrier/", "/brands/super-general/"):
            with self.subTest(path=path):
                r = self.client.get(path)
                self.assertNotContains(r, "Origin:")
                self.assertNotContains(r, "المنشأ")


class CategoryAdminDraftTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)
        from django.contrib.auth import get_user_model
        cls.admin = get_user_model().objects.create_superuser("admin", "admin@example.com", "pw")

    def setUp(self):
        self.client.force_login(self.admin)

    def test_edit_view_offers_draft_publish_and_preview(self):
        from django.urls import reverse
        cat = ProductCategory.objects.get(slug="window")
        r = self.client.get(reverse("wagtailsnippets_catalog_productcategory:edit", args=[cat.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Publish")
        self.assertContains(r, "Save draft")
        self.assertContains(r, reverse("wagtailsnippets_catalog_productcategory:preview_on_edit", args=[cat.pk]))
        # Supply rows expose the new fields
        self.assertContains(r, "source_type")
        self.assertContains(r, "nominal_tons_min")
