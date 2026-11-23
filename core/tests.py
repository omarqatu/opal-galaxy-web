from django.core.management import call_command
from django.test import TestCase, override_settings

from catalog.models import Brand, ProductCategory, Supply
from core.models import QuoteRequest


class SiteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def test_seed_counts(self):
        self.assertEqual(Brand.objects.count(), 11)
        self.assertEqual(ProductCategory.objects.count(), 10)
        self.assertEqual(Supply.objects.count(), 36)

    def test_every_page_renders_in_both_languages(self):
        paths = ["/", "/maintenance/"]
        paths += [f"/products/{c.slug}/" for c in ProductCategory.objects.all()]
        paths += [f"/brands/{b.slug}/" for b in Brand.objects.all()]
        for p in paths:
            for prefix, lang in (("", "en"), ("/ar", "ar")):
                with self.subTest(path=prefix + p):
                    r = self.client.get(prefix + p)
                    self.assertEqual(r.status_code, 200)
                    self.assertContains(r, f'<html lang="{lang}"')

    def test_arabic_is_rtl_and_translated(self):
        r = self.client.get("/ar/products/window/")
        self.assertContains(r, 'dir="rtl"')
        self.assertContains(r, "وحدات شباك")

    def test_unknown_product_404(self):
        self.assertEqual(self.client.get("/products/does-not-exist/").status_code, 404)

    def test_quote_saved_and_redirects_back(self):
        r = self.client.post("/quote/", {"phone": "+971 50 123 4567", "name": "Test", "unit": "vrf",
                                         "brand": "carrier", "qty": "12", "install": "yes",
                                         "lang": "ar", "source_page": "/ar/products/vrf/"})
        self.assertRedirects(r, "/ar/products/vrf/?sent=1#contact", fetch_redirect_response=False)
        q = QuoteRequest.objects.get()
        self.assertEqual((q.product, q.brand, q.quantity, q.installation, q.language), ("vrf", "carrier", 12, True, "ar"))

    def test_quote_rejects_missing_phone(self):
        r = self.client.post("/quote/", {"phone": "12", "source_page": "/"})
        self.assertRedirects(r, "/?sent=0#contact", fetch_redirect_response=False)
        self.assertFalse(QuoteRequest.objects.exists())

    def test_quote_honeypot_drops_bots(self):
        self.client.post("/quote/", {"phone": "+971501234567", "website": "spam.example"})
        self.assertFalse(QuoteRequest.objects.exists())

    def test_quote_redirect_cannot_leave_site(self):
        r = self.client.post("/quote/", {"phone": "+971501234567", "source_page": "https://evil.example/x"})
        self.assertRedirects(r, "/?sent=1#contact", fetch_redirect_response=False)

    @override_settings(SITE_NOINDEX=True)
    def test_preview_is_noindex(self):
        self.assertEqual(self.client.get("/").headers["X-Robots-Tag"], "noindex, nofollow")
        self.assertIn("Disallow: /", self.client.get("/robots.txt").content.decode())

    @override_settings(SITE_NOINDEX=False, SITE_BASE_URL="https://opal-galaxy.com")
    def test_production_sitemap(self):
        r = self.client.get("/sitemap.xml")
        self.assertContains(r, "https://opal-galaxy.com/ar/brands/coolex/")
        self.assertNotIn("X-Robots-Tag", self.client.get("/").headers)


class CatalogAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)
        from django.contrib.auth import get_user_model
        cls.admin = get_user_model().objects.create_superuser("admin", "admin@example.com", "pw")

    def setUp(self):
        self.client.force_login(self.admin)

    def test_menu_has_products_and_brands(self):
        r = self.client.get("/admin/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Products")
        self.assertContains(r, "Brands")

    def test_products_listing_shows_both_names(self):
        from django.urls import reverse
        r = self.client.get(reverse("wagtailsnippets_catalog_productcategory:list"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Window units")
        self.assertContains(r, "وحدات شباك")

    def test_brands_listing_works(self):
        from django.urls import reverse
        r = self.client.get(reverse("wagtailsnippets_catalog_brand:list"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Carrier")
        self.assertNotContains(r, "الولايات المتحدة")  # country of origin removed


class DesignFoundationTests(TestCase):
    """Phase 1 of the redesign: fonts, tokens, fixed labels, error pages, new brands."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def test_fonts_are_self_hosted(self):
        html = self.client.get("/").content.decode()
        self.assertNotIn("fonts.googleapis.com", html)
        self.assertNotIn("fonts.gstatic.com", html)
        self.assertIn("css/tokens.css", html)
        self.assertIn("fonts/ibm-plex-sans-latin-400-normal.woff2", html)
        self.assertIn("fonts/ibm-plex-sans-arabic-400-normal.woff2", self.client.get("/ar/").content.decode())

    def test_every_font_file_in_the_stylesheet_exists(self):
        import re
        from django.conf import settings
        css = (settings.BASE_DIR / "static/css/tokens.css").read_text()
        urls = re.findall(r'url\("([^"]+)"\)', css)
        self.assertEqual(len(urls), 8)
        for u in urls:
            self.assertTrue((settings.BASE_DIR / "static/css" / u).resolve().is_file(), u)

    def test_text_colours_meet_wcag_aa(self):
        import re
        from django.conf import settings
        css = (settings.BASE_DIR / "static/css/tokens.css").read_text()
        tok = dict(re.findall(r"--([a-z0-9-]+):(#[0-9A-Fa-f]{6})", css))

        def lum(h):
            ch = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        def ratio(a, b):
            hi, lo = sorted((lum(tok[a]), lum(tok[b])), reverse=True)
            return (hi + 0.05) / (lo + 0.05)

        pairs = [("navy", "white"), ("navy", "off-white"), ("muted", "white"), ("muted", "off-white"),
                 ("cyan-ink", "white"), ("cyan-ink", "off-white"), ("navy", "cyan"), ("navy", "sky"),
                 ("navy", "sand"), ("navy", "wa"), ("sky", "navy"), ("cyan", "navy"), ("white", "navy")]
        for fg, bg in pairs:
            with self.subTest(fg=fg, bg=bg):
                self.assertGreaterEqual(ratio(fg, bg), 4.5)
        # Light cyan on white is not readable: it must never be a text colour.
        self.assertLess(ratio("cyan", "white"), 4.5)

    def test_fixed_labels_are_translated(self):
        self.assertContains(self.client.get("/products/wall/"), ">Home</a>")
        self.assertContains(self.client.get("/ar/products/wall/"), ">الرئيسية</a>")
        self.assertContains(self.client.get("/ar/"), "الانتقال إلى المحتوى")

    def test_404_is_branded_in_both_languages(self):
        r = self.client.get("/no-such-page/")
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, "Page not found", status_code=404)
        self.assertContains(r, 'class="error-page"', status_code=404)
        self.assertNotContains(r, 'id="quote"', status_code=404)
        r = self.client.get("/ar/no-such-page/")
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, 'dir="rtl"', status_code=404)
        self.assertContains(r, "الصفحة غير موجودة", status_code=404)

    def test_500_is_branded_and_uses_no_database(self):
        from django.test import RequestFactory
        from core.views import server_error
        for path, lang, text in (("/x/", "en", "Something went wrong"), ("/ar/x/", "ar", "حدث خطأ غير متوقع")):
            with self.subTest(path=path), self.assertNumQueries(0):
                r = server_error(RequestFactory().get(path))
                self.assertEqual(r.status_code, 500)
                body = r.content.decode()
                self.assertIn(f'<html lang="{lang}"', body)
                self.assertIn(text, body)
                self.assertNotIn("Traceback", body)

    @override_settings(DEBUG=False)
    def test_unhandled_error_returns_the_500_page(self):
        from unittest import mock
        self.client.raise_request_exception = False
        with mock.patch("core.views.HttpResponse", side_effect=RuntimeError("boom")):
            r = self.client.get("/health")
        self.assertEqual(r.status_code, 500)
        self.assertIn("Something went wrong", r.content.decode())
        self.assertNotIn("boom", r.content.decode())

    def test_new_brands_have_pages_with_no_invented_content(self):
        for slug, name in (("skm", "SKM"), ("lg", "LG"), ("daikin", "Daikin"), ("trane", "Trane")):
            b = Brand.objects.get(slug=slug)
            self.assertEqual((b.name, b.line_en, b.about_en, b.supplies.count()), (name, "", "", 0))
            for prefix in ("", "/ar"):
                r = self.client.get(f"{prefix}/brands/{slug}/")
                self.assertEqual(r.status_code, 200)
                self.assertNotContains(r, 'class="supply"')
        self.assertContains(self.client.get("/sitemap.xml"), "/brands/trane/")

    def test_brand_page_states_no_count(self):
        self.assertNotContains(self.client.get("/brands/carrier/"), "product types")

    def test_category_icons_exist_for_every_category(self):
        from core.templatetags.opal import cat_icon
        for slug in ("wall", "window", "ducted", "cassette", "floor-ceiling", "floor-standing",
                     "package", "vrf", "chillers-ahu"):
            self.assertIn("<svg", cat_icon(slug), slug)
        self.assertEqual(cat_icon("not-a-category"), "")

    @override_settings(SITE_NOINDEX=True)
    def test_styleguide_on_staging_in_both_languages(self):
        self.assertContains(self.client.get("/styleguide/"), "Deep Navy")
        self.assertContains(self.client.get("/ar/styleguide/"), 'dir="rtl"')
        self.assertNotContains(self.client.get("/sitemap.xml"), "styleguide")

    @override_settings(SITE_NOINDEX=False)
    def test_styleguide_hidden_on_an_indexed_site(self):
        self.assertEqual(self.client.get("/styleguide/").status_code, 404)


class AddBrandsMigrationTests(TestCase):
    """catalog 0003: adds four brands to a site that has content, and changes nothing else."""

    def run_migration(self):
        import importlib
        from django.apps import apps
        mod = importlib.import_module("catalog.migrations.0003_add_brands_skm_lg_daikin_trane")
        mod.add_brands(apps, None)

    def test_empty_database_is_left_to_the_seed(self):
        self.run_migration()
        self.assertFalse(Brand.objects.exists())

    def test_adds_missing_brands_after_the_existing_ones_and_is_idempotent(self):
        Brand.objects.create(slug="carrier", name="Carrier", sort_order=0, about_en="Keep me")
        Brand.objects.create(slug="lg", name="LG Electronics", sort_order=6, about_en="Edited by Omar")
        self.run_migration()
        self.run_migration()
        self.assertEqual(list(Brand.objects.values_list("slug", "name", "sort_order")),
                         [("carrier", "Carrier", 0), ("lg", "LG Electronics", 6),
                          ("skm", "SKM", 7), ("daikin", "Daikin", 8), ("trane", "Trane", 9)])
        self.assertEqual(Brand.objects.get(slug="lg").about_en, "Edited by Omar")
        self.assertEqual(Brand.objects.get(slug="carrier").about_en, "Keep me")
