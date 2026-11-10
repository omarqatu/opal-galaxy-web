from django.core.management import call_command
from django.test import TestCase, override_settings

from catalog.models import Brand, ProductCategory, Supply
from core.models import QuoteRequest


class SiteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def test_seed_counts(self):
        self.assertEqual(Brand.objects.count(), 7)
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
        self.assertContains(r, "الولايات المتحدة")
