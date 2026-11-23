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


class HomeRedesignTests(TestCase):
    """Phase 2 of the redesign: the home page, site chrome and quote section."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def test_hero_copy_and_buttons_come_from_wagtail(self):
        from core.models import HomePage
        en, ar = self.client.get("/"), self.client.get("/ar/")
        self.assertContains(en, '<h1>Engineered Cooling. <span class="accent">Delivered with Confidence.</span></h1>')
        self.assertContains(en, "Explore HVAC Solutions")
        self.assertContains(en, "Request a Project Quote")
        self.assertContains(ar, 'تكييف بمعايير هندسية، <span class="accent">وتنفيذ جدير بالثقة</span>')
        self.assertContains(ar, "استكشاف حلول التكييف")
        home = HomePage.objects.get()
        home.hero_cta_primary_en = "See the equipment"
        home.save()
        self.assertContains(self.client.get("/"), "See the equipment")

    def test_no_hardcoded_counts_and_new_email(self):
        for path in ("/", "/ar/"):
            html = self.client.get(path).content.decode()
            for banned in ("Seven brands", "Ten equipment", "سبع علامات", "عشرة أنواع", "opalgalaxyac@gmail.com"):
                self.assertNotIn(banned, html)
            self.assertIn("mailto:info@opalgalaxy.ae", html)
        self.assertContains(self.client.get("/"), "A wide range of equipment types")
        self.assertContains(self.client.get("/ar/"), "مجموعة واسعة من أنواع المعدات")

    def test_brand_wall_lists_every_brand_without_logos(self):
        html = self.client.get("/").content.decode()
        wall = html.split('class="brand-wall"')[1].split("</ul>")[0]
        self.assertEqual(wall.count('class="brand-tile"'), Brand.objects.count())
        self.assertNotIn("<img", wall)
        self.assertNotIn("marquee", html)

    def test_categories_come_from_the_cms_with_icons(self):
        html = self.client.get("/ar/").content.decode()
        grid = html.split('class="cat-cards"')[1].split("</section>")[0]
        self.assertEqual(grid.count('class="cat-card"'), ProductCategory.objects.live().count())
        self.assertEqual(grid.count("<img"), ProductCategory.objects.live().exclude(image=None).count())
        self.assertIn("<svg", grid)   # a category without an image falls back to its line icon
        self.assertIn("وحدات شباك", grid)
        self.assertIn('href="/ar/products/vrf/"', grid)

    def test_services_process_and_duct_cleaning(self):
        en, ar = self.client.get("/").content.decode(), self.client.get("/ar/").content.decode()
        for title in ("HVAC supply", "Installation", "Maintenance and spare parts", "AC duct cleaning",
                      "Project quotations", "Contractor and commercial project support",
                      "Project consultation and site assessment", "Equipment supply and installation",
                      "Testing, commissioning and handover", "BOQ support", "Warranty documentation"):
            self.assertIn(title, en)
        self.assertIn("تنظيف مجاري التكييف", ar)
        self.assertIn('href="/maintenance/"', en.split('id="services"')[1].split("</section>")[0])
        self.assertIn('href="/duct-cleaning/">Ask about duct cleaning', en)
        self.assertIn('href="/ar/duct-cleaning/">الاستفسار عن تنظيف مجاري التكييف', ar)

    def test_unverified_claims_are_not_headlines(self):
        html = self.client.get("/").content.decode()
        self.assertNotIn('class="facts"', html)
        self.assertNotIn("<h3>Volume quote within one working day</h3>", html)
        self.assertNotIn("Delivery within 48 hours", html)   # no longer shown at the top of the page
        self.assertIn("within 48 hours in Dubai", html)      # still stated in the FAQ answer
        from core.models import HomeFact
        self.assertEqual(HomeFact.objects.count(), 3)        # the records themselves are kept

    def test_gallery_links_open_the_photo_without_javascript(self):
        html = self.client.get("/").content.decode()
        self.assertEqual(html.count("data-lightbox"), 8)
        self.assertRegex(html, r'<a class="frame" href="/media/images/[^"]+" data-lightbox')
        self.assertIn('<dialog class="lightbox"', html)

    def test_all_questions_are_preserved_and_can_be_unfeatured(self):
        from core.models import FaqItem
        self.assertEqual(self.client.get("/").content.decode().count("<details>"), 6)
        FaqItem.objects.filter(question_en__startswith="How long").update(featured=False)
        html = self.client.get("/").content.decode()
        self.assertEqual(html.count("<details>"), 5)
        self.assertEqual(FaqItem.objects.count(), 6)

    def test_quote_form_keeps_every_field_and_its_endpoint(self):
        html = self.client.get("/ar/products/vrf/").content.decode()
        form = html.split('<form id="quote"')[1].split("</form>")[0]
        self.assertIn('method="post" action="/quote/"', form)
        for name in ("csrfmiddlewaretoken", "lang", "source_page", "website", "name", "phone", "type", "unit",
                     "brand", "qty", "emirate", "install", "notes"):
            self.assertIn(f'name="{name}"', form)
        self.assertIn('<option value="vrf" data-brands="', form)
        self.assertIn("هل يشمل الطلب التركيب؟", form)
        self.assertIn("طلب عرض سعر لمشروعكم", html)
        r = self.client.post("/quote/", {"phone": "+971501234567", "source_page": "/"}, follow=True)
        self.assertContains(r, "Your request has been sent. Thank you.")
        self.assertNotContains(r, "within one working day.</div>")

    def test_privacy_note_links_to_the_policy_once_the_page_exists(self):
        from core.models import HomePage, ServicePage
        from wagtail.models import Page
        self.assertContains(self.client.get("/"), '<a href="/privacy/">We never share your details.</a>')
        self.assertContains(self.client.get("/ar/"), 'href="/ar/privacy/"')
        Page.objects.get(slug="privacy").specific.unpublish()
        self.assertContains(self.client.get("/"), '<span class="alt">We never share your details.</span>')

    def test_social_icons_link_only_when_a_url_is_set(self):
        from core.models import CompanySettings
        html = self.client.get("/").content.decode()
        social = html.split('class="social"')[1].split("</ul>")[0]
        self.assertEqual(social.count("<svg"), 4)
        self.assertNotIn("<a", social)
        self.assertNotIn('href="#"', html)
        cs = CompanySettings.load()
        cs.instagram_url = "https://www.instagram.com/example"
        cs.save()
        social = self.client.get("/").content.decode().split('class="social"')[1].split("</ul>")[0]
        self.assertEqual(social.count("<a "), 1)
        self.assertIn('href="https://www.instagram.com/example"', social)

    def test_menu_and_footer_texts_are_editable_site_texts(self):
        from core.models import SiteCopy
        self.assertContains(self.client.get("/ar/"), "المقاولون والمشاريع")
        copy = SiteCopy.load()
        copy.nav_quote_en, copy.footer_hours_ar = "Get a quote", "أوقات الدوام"
        copy.save()
        self.assertContains(self.client.get("/products/wall/"), "Get a quote")
        self.assertContains(self.client.get("/ar/"), "أوقات الدوام")

    def test_existing_destinations_are_still_in_the_menu(self):
        html = self.client.get("/products/wall/").content.decode()
        menu = html.split('id="menu"')[1].split("</nav>")[0]
        for href in ('"/"', '/#products"', '/#brands"', '/#contractors"', '/#install"', '"/maintenance/"',
                     '"/duct-cleaning/"', '"/about/"', '"/contact/"'):
            self.assertIn(href, menu)

    def test_one_h1_and_no_external_requests(self):
        import re
        for path in ("/", "/ar/"):
            html = self.client.get(path).content.decode()
            self.assertEqual(html.count("<h1"), 1)
            for url in re.findall(r'(?:src|href)="(https?://[^"]+)"', html):
                self.assertTrue(url.startswith(("https://wa.me/", "http://testserver")), url)


class HomeContentMigrationTests(TestCase):
    """core 0003 writes the approved copy into an existing site without touching edited texts."""

    def apply(self):
        import importlib
        from django.apps import apps
        importlib.import_module("core.migrations.0003_redesign_home_content").apply_content(apps, None)

    def seed_original(self):
        """The site as it was before the redesign: the seed without the content migrations."""
        from unittest import mock
        with mock.patch("importlib.import_module") as imp:
            call_command("seed_site", verbosity=0)
        self.assertTrue(imp.called)

    def test_empty_database_is_left_alone(self):
        from core.models import CompanySettings, HomePage
        self.apply()
        self.assertFalse(HomePage.objects.exists())
        self.assertFalse(CompanySettings.objects.exists())

    def test_original_site_gets_the_new_copy_on_the_page_and_in_its_latest_revision(self):
        from core.models import CompanySettings, HomePage
        self.seed_original()
        home = HomePage.objects.get()
        self.assertEqual(home.hero_title_en, "Air conditioning, supplied at project scale")
        self.assertEqual(CompanySettings.load().email, "opalgalaxyac@gmail.com")
        faqs_before = list(home.faqs.values_list("question_en", "answer_ar"))
        gallery_before = list(home.gallery.values_list("image_id", "caption_en"))
        self.apply()
        home = HomePage.objects.get()
        draft = home.get_latest_revision_as_object()
        for obj in (home, draft):
            self.assertEqual(obj.hero_title_en, "Engineered Cooling. Delivered with Confidence.")
            self.assertEqual(obj.hero_image.title, "Gallery: Two inverter condensers beside a villa")
            self.assertEqual(obj.contractors_image.title, "Gallery: Crane lifting a package unit onto a roof")
            self.assertEqual(obj.hero_caption_en, "")
            self.assertEqual([p.title_en for p in obj.contractor_points.all()][0], "Project quotations")
            self.assertEqual(obj.contractor_points.count(), 7)
            self.assertEqual(obj.services.count(), 6)
            self.assertEqual([s.title_ar for s in obj.install_steps.all()],
                             ["استشارة المشروع ومعاينة الموقع", "توريد المعدات وتركيبها", "الاختبار والتشغيل والتسليم"])
            self.assertEqual(obj.install_steps.first().text_en,
                             "We measure area, orientation and insulation, then recommend tonnage and type.")
        self.assertEqual(home.services.get(icon="parts").link_page.slug, "maintenance")
        self.assertEqual(CompanySettings.load().email, "info@opalgalaxy.ae")
        self.assertEqual(list(home.faqs.values_list("question_en", "answer_ar")), faqs_before)
        self.assertEqual(list(home.gallery.values_list("image_id", "caption_en")), gallery_before)
        self.assertEqual(home.about_text_en.count("licensed air-conditioning trading company"), 1)

    def test_edited_texts_lists_and_images_are_never_overwritten(self):
        from wagtail.images.models import Image
        from core.models import CompanySettings, ContractorPoint, HomePage
        self.seed_original()
        home = HomePage.objects.get()
        home.hero_title_en = "Omar's own headline"
        home.hero_cta_primary_en = "Omar's button"
        home.hero_image = Image.objects.get(title="Gallery: Batch of boxed units on a residential site")
        home.save()
        ContractorPoint.objects.filter(page=home, sort_order=0).update(title_en="Edited point")
        cs = CompanySettings.load()
        cs.email = "sales@example.com"
        cs.save()
        self.apply()
        home = HomePage.objects.get()
        self.assertEqual(home.hero_title_en, "Omar's own headline")
        self.assertEqual(home.hero_cta_primary_en, "Omar's button")
        self.assertEqual(home.hero_cta_secondary_en, "Request a Project Quote")
        self.assertEqual(home.hero_image.title, "Gallery: Batch of boxed units on a residential site")
        self.assertEqual(home.hero_alt_en, "Rooftop package air-conditioning units on a commercial building in Dubai")
        self.assertEqual(home.contractor_points.count(), 4)
        self.assertEqual(home.contractor_points.first().title_en, "Edited point")
        self.assertEqual(CompanySettings.load().email, "sales@example.com")

    def test_running_twice_changes_nothing_more(self):
        from core.models import HomePage, HomeService
        self.seed_original()
        self.apply()
        home = HomePage.objects.get()
        home.services.all().delete()
        HomeService.objects.create(page=home, sort_order=0, title_en="Only one")
        home.duct_title_en = ""
        home.save()
        before = (home.contractor_points.count(), home.hero_title_ar)
        self.apply()
        home = HomePage.objects.get()
        self.assertEqual((home.contractor_points.count(), home.hero_title_ar), before)
        self.assertEqual(home.services.count(), 1)
        # A field the operator emptied is filled again only because it is empty: documented behaviour.
        self.assertEqual(home.duct_title_en, "AC duct cleaning")


class InternalPagesTests(TestCase):
    """Phase 3 of the redesign: category, brand and service pages, and the five new pages."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    NEW = ("duct-cleaning", "contact", "faq", "about", "privacy")

    def test_new_pages_exist_in_both_languages_with_canonical_and_hreflang(self):
        for slug in self.NEW:
            for prefix, lang in (("", "en"), ("/ar", "ar")):
                with self.subTest(slug=slug, lang=lang):
                    r = self.client.get(f"{prefix}/{slug}/")
                    self.assertEqual(r.status_code, 200)
                    html = r.content.decode()
                    self.assertIn(f'<html lang="{lang}"', html)
                    self.assertEqual(html.count("<h1"), 1)
                    self.assertIn(f'<link rel="canonical" href="http://testserver{prefix}/{slug}/">', html)
                    self.assertIn(f'hreflang="en" href="http://testserver/{slug}/"', html)
                    self.assertIn(f'hreflang="ar" href="http://testserver/ar/{slug}/"', html)

    def test_new_pages_are_in_the_sitemap_and_existing_urls_are_kept(self):
        xml = self.client.get("/sitemap.xml").content.decode()
        for slug in self.NEW + ("maintenance",):
            self.assertIn(f"<loc>http://testserver/{slug}/</loc>", xml)
            self.assertIn(f"<loc>http://testserver/ar/{slug}/</loc>", xml)
        for path in ("/products/vrf/", "/brands/carrier/", "/maintenance/"):
            self.assertEqual(self.client.get(path).status_code, 200)

    def test_duct_cleaning_uses_the_approved_arabic_name_and_invents_nothing(self):
        en = self.client.get("/duct-cleaning/").content.decode()
        ar = self.client.get("/ar/duct-cleaning/").content.decode()
        self.assertIn("<h1>تنظيف مجاري التكييف</h1>", ar)
        self.assertIn('<option value="duct-cleaning" selected>AC duct cleaning</option>', en)
        body = en.split('id="app"')[1].split('id="contact"')[0]
        for banned in ("AED", "hours", "guarantee", "certified", "warranty", "%"):
            self.assertNotIn(banned, body)

    def test_duct_cleaning_request_is_saved_with_its_service(self):
        self.client.post("/quote/", {"phone": "+971501234567", "unit": "duct-cleaning",
                                     "source_page": "/duct-cleaning/"})
        self.assertEqual(QuoteRequest.objects.get().product, "duct-cleaning")

    def test_faq_page_shows_every_question_even_when_not_featured(self):
        from core.models import FaqItem
        FaqItem.objects.update(featured=False)
        html = self.client.get("/ar/faq/").content.decode()
        self.assertEqual(html.split('class="accordion"')[1].split("</section>")[0].count("<details"), 6)
        self.assertIn("ما معنى تصنيف T3", html)

    def test_contact_page_shows_company_details_and_the_form(self):
        html = self.client.get("/contact/").content.decode()
        for text in ("tel:+971541981593", "mailto:info@opalgalaxy.ae", "Port Saeed", 'id="quote"', "wa.me/971541981593"):
            self.assertIn(text, html)

    def test_about_page_repeats_the_existing_company_text_only(self):
        from core.models import HomePage
        home = HomePage.objects.get()
        html = self.client.get("/about/").content.decode()
        first, second = [p.strip() for p in home.about_text_en.split("\n\n")]
        self.assertIn(first, html)
        self.assertIn(second.replace("\u2019", "&#x27;"), html.replace("’", "&#x27;") if "\u2019" in second else html)
        self.assertIn('href="/about/"', self.client.get("/").content.decode())

    def test_privacy_policy_states_only_what_the_site_does(self):
        en = self.client.get("/privacy/").content.decode()
        body = en.split('id="app"')[1].split("<footer")[0]
        for text in ("Phone number", "Quantity", "Emirate", "saved in the website", "one cookie", "Cloudflare",
                     "info@opalgalaxy.ae"):
            self.assertIn(text, body)
        for banned in ("GDPR", "PDPL", "Federal Decree", "days", "months", "years", "Google Analytics", "pixel"):
            self.assertNotIn(banned, body)
        self.assertIn("سياسة الخصوصية", self.client.get("/ar/privacy/").content.decode())

    def test_category_page_has_no_counts_and_keeps_catalogue_rows_verbatim(self):
        en = self.client.get("/products/vrf/").content.decode()
        ar = self.client.get("/ar/products/vrf/").content.decode()
        for html in (en, ar):
            self.assertNotIn("Available from <b>", html)
            self.assertNotIn("علامات تجارية</span>", html)
            for s in Supply.objects.filter(category__slug="vrf"):
                self.assertIn(s.models_text.replace("&", "&amp;"), html)
        self.assertIn('<div class="supply-row__data" dir="ltr" lang="en">', ar)
        self.assertNotIn("vrf systems", en)   # the old lower-cased button text
        self.assertIn("Request a quote for this equipment", en)

    def test_brand_page_texts_come_from_site_texts(self):
        from core.models import SiteCopy
        self.assertContains(self.client.get("/brands/carrier/"), "What we supply from Carrier")
        self.assertContains(self.client.get("/ar/brands/carrier/"), "ما نورّده من Carrier")
        copy = SiteCopy.load()
        copy.brand_supply_title_en = "{name}: our range"
        copy.save()
        self.assertContains(self.client.get("/brands/carrier/"), "Carrier: our range")

    def test_arabic_language_corrections(self):
        from core.models import ServiceItem
        ar = self.client.get("/ar/").content.decode()
        for banned in ("(Ducted)", "(Package)", "مجاري الهواء", "(BOQ)", "(Submittals)", "46° مئوية",
                       "الخيار خليجي الصنع", "وحدتان Inverter<"):
            self.assertNotIn(banned, ar)
        self.assertIn("مجاري التكييف", ar)
        self.assertIn("شيلرات ووحدات مناولة الهواء وفان كويل", ar)
        self.assertIn("46 °م", ar)
        self.assertNotIn("مجاري الهواء", self.client.get("/ar/products/package/").content.decode())
        self.assertFalse(ServiceItem.objects.filter(text_en__contains="seven brands").exists())
        self.assertNotIn("السبع", self.client.get("/ar/maintenance/").content.decode())

    def test_catalogue_rows_are_untouched_by_the_content_migrations(self):
        import json
        from django.conf import settings
        seed = json.loads((settings.BASE_DIR / "seed/opal.json").read_text(encoding="utf-8"))
        for cat in seed["categories"]:
            for row in cat.get("supply", []):
                s = Supply.objects.get(category__slug=cat["slug"], brand__slug=row["brand"])
                self.assertEqual((s.models_text, s.specs), (row["models"], "\n".join(row.get("specs", []))))


class PagesContentMigrationTests(TestCase):
    """core 0005: creates the new pages once and corrects phrases only where they still stand."""

    def apply(self):
        import importlib
        from django.apps import apps
        importlib.import_module("core.migrations.0005_redesign_pages_content").apply_content(apps, None)

    def test_empty_database_is_left_alone(self):
        from wagtail.models import Page
        before = Page.objects.count()
        self.apply()
        self.assertEqual(Page.objects.count(), before)

    def test_idempotent_and_respects_edits_and_existing_pages(self):
        from wagtail.models import Page
        from catalog.models import ProductCategory
        from core.models import ContentPage, ContentSection, HomePage
        call_command("seed_site", verbosity=0)
        pages, sections = Page.objects.count(), ContentSection.objects.count()
        privacy = ContentPage.objects.get(slug="privacy")
        privacy.sections.all().delete()
        privacy.lead_en = "Edited by Omar"
        privacy.save()
        ducted = ProductCategory.objects.get(slug="ducted")
        ducted.name_ar = "وحدات مخفية"
        ducted.lead_ar = "نص كتبه عمر عن مجاري الهواء"   # a later edit that uses the old term on purpose
        ducted.save()
        home = HomePage.objects.get()
        home.faq_page = None
        home.about_page = Page.objects.get(slug="contact")
        home.save()
        self.apply()
        self.assertEqual(Page.objects.count(), pages)
        self.assertEqual(ContentSection.objects.count(), sections - 8)
        self.assertEqual(ContentPage.objects.get(slug="privacy").lead_en, "Edited by Omar")
        home = HomePage.objects.get()
        self.assertEqual(home.about_page.slug, "contact")   # an operator's choice is kept
        self.assertEqual(home.faq_page.slug, "faq")         # an empty link is filled
        # Treebeard bookkeeping stays consistent after pages created by the migration.
        self.assertEqual(home.numchild, home.get_children().count())
        self.assertEqual(Page.find_problems(), ([], [], [], [], []))

    def test_latest_revisions_get_the_corrections_too(self):
        from catalog.models import ProductCategory
        from core.models import HomePage
        call_command("seed_site", verbosity=0)
        draft = HomePage.objects.get().get_latest_revision_as_object()
        self.assertIn("بوصفها حلقة وصل", draft.about_text_ar)
        self.assertEqual(draft.duct_page.slug, "duct-cleaning")
        self.assertIn("46 °م", " ".join(f.answer_ar for f in draft.faqs.all()))
        self.assertEqual(ProductCategory.objects.get(slug="ducted").name_ar, "وحدات مخفية")


class PremiumHomeTests(TestCase):
    """The approved premium composition: navy header, hero illustration, category tiles."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def test_header_uses_the_original_logo_file_and_keeps_every_action(self):
        import hashlib
        from django.conf import settings
        html = self.client.get("/ar/").content.decode()
        header = html.split('<header id="site-header"')[1].split("</header>")[0]
        self.assertIn("img/opal-galaxy-logo-v1-reversed.svg", header)
        self.assertIn('href="tel:+971541981593"', header)
        self.assertIn("https://wa.me/971541981593", header)
        self.assertIn('hreflang="en"', header)
        self.assertIn('class="submenu"', header)
        self.assertEqual(header.count('/ar/products/'), ProductCategory.objects.live().count())
        self.assertEqual(header.count('/ar/brands/'), Brand.objects.count())
        # The logo artwork is the file that was already in the repository, byte for byte.
        digests = {n: hashlib.sha256((settings.BASE_DIR / "static/img" / n).read_bytes()).hexdigest()
                   for n in ("opal-galaxy-logo-v1.svg", "opal-galaxy-logo-v1-reversed.svg")}
        self.assertEqual(digests, {
            "opal-galaxy-logo-v1.svg": "f42f23107c91e15c794bbfc317b7dd863dbf083f636fcea3c442429c613f008a",
            "opal-galaxy-logo-v1-reversed.svg": "d5b0300b124f56a48840d6f64e2d4dd5b80ee9b0cf21817106bac55aed759681"})

    def test_hero_has_eyebrow_highlights_and_responsive_illustration(self):
        from core.models import HomePage
        en, ar = self.client.get("/").content.decode(), self.client.get("/ar/").content.decode()
        hero = en.split('class="hero-x"')[1].split("</section>")[0]
        self.assertIn("HVAC supply · Installation · Project support", hero)
        self.assertEqual(hero.count("<li>"), 3)
        for text in ("HVAC supply and installation", "Maintenance and spare parts", "Project and contractor support"):
            self.assertIn(text, hero)
        self.assertIn('<source media="(max-width:860px)"', hero)
        self.assertRegex(hero, r'<img src="/media/images/hero-rooftop[^"]+\.webp" srcset="[^"]+ 1000w, [^"]+ \d+w"')
        self.assertIn('alt="Illustration: a technician servicing rooftop air-conditioning units"', hero)
        self.assertIn('fetchpriority="high"', hero)
        self.assertIn("صورة توضيحية", ar)
        self.assertIn("دعم المشاريع والمقاولين", ar)
        self.assertLess(hero.index('href="#contact"'), hero.index('href="#products"'))  # quote first
        home = HomePage.objects.get()
        home.hero_eyebrow_en = "Edited eyebrow"
        home.save()
        self.assertContains(self.client.get("/"), "Edited eyebrow")

    def test_illustration_is_not_presented_as_a_project(self):
        from core.models import HomePage
        home = HomePage.objects.get()
        self.assertNotIn(home.hero_image_id, list(home.gallery.values_list("image_id", flat=True)))
        self.assertEqual(home.hero_caption_en, "")
        gallery = self.client.get("/").content.decode().split('id="gallery"')[1].split("</ul>")[0]
        self.assertNotIn("hero-rooftop", gallery)

    def test_category_cards_never_show_tons_and_never_convert(self):
        from core.templatetags.opal import card_range
        shown = {c.slug: card_range(c) for c in ProductCategory.objects.all()}
        self.assertEqual(shown["wall"], "9,000 – 36,000 BTU")
        self.assertEqual(shown["vrf"], "4 – 80 HP per system")      # as stored; the operator edits it
        for slug in ("ducted", "package", "chillers-ahu"):
            self.assertEqual(shown[slug], "", slug)                   # stored in tons: not shown
        ducted = ProductCategory.objects.get(slug="ducted")
        ducted.capacity_range = "12,000-336,000"                      # a plain figure is shown as it is
        ducted.save()
        self.assertEqual(card_range(ducted), "12,000-336,000")
        cards = self.client.get("/ar/").content.decode().split('class="cat-cards"')[1].split("</ul>")[0]
        self.assertIn("9,000 – 36,000 BTU", cards)
        self.assertIn("12,000-336,000", cards)
        self.assertNotIn("ton", cards)
        self.assertNotIn("طن", cards)
        self.assertIn("السعة", cards)
        self.assertEqual(ProductCategory.objects.get(slug="package").capacity_range, "3 – 100 ton")  # stored value kept

    def test_accent_filter_escapes_and_plain_strips(self):
        from core.templatetags.opal import accent, plain
        self.assertEqual(accent("A <b> *C & D*"), 'A &lt;b&gt; <span class="accent">C &amp; D</span>')
        self.assertEqual(accent("No markers"), "No markers")
        self.assertEqual(plain("One *two*"), "One two")


class HeroContentMigrationTests(TestCase):
    """core 0007: adds the illustrations and highlights; replaces only what phase 2 put there."""

    def apply(self):
        import importlib
        from django.apps import apps
        importlib.import_module("core.migrations.0007_home_hero_content").apply_content(apps, None)

    def test_empty_database_is_left_alone(self):
        from wagtail.images.models import Image
        self.apply()
        self.assertFalse(Image.objects.exists())

    def test_seeded_site_gets_the_illustration_once_and_revision_matches(self):
        from wagtail.images.models import Image
        from core.models import HomePage
        call_command("seed_site", verbosity=0)
        images = Image.objects.count()
        self.apply()
        self.assertEqual(Image.objects.count(), images)
        home = HomePage.objects.get()
        for obj in (home, home.get_latest_revision_as_object()):
            self.assertEqual(obj.hero_image.title, "Home hero illustration (rooftop, wide)")
            self.assertEqual(obj.hero_image_mobile.title, "Home hero illustration (rooftop, 4:3)")
            self.assertEqual(obj.hero_title_en, "Engineered Cooling. *Delivered with Confidence.*")
            self.assertEqual(obj.highlights.count(), 3)
        self.assertEqual((home.hero_image.width, home.hero_image.height), (2000, 1125))
        self.assertTrue(home.hero_image.file.storage.exists(home.hero_image.file.name))
        self.assertEqual(home.hero_lead_en[:12], "Premium HVAC")   # other texts untouched

    def test_operator_choices_are_kept(self):
        from wagtail.images.models import Image
        from core.models import HomeHighlight, HomePage
        call_command("seed_site", verbosity=0)
        home = HomePage.objects.get()
        own = Image.objects.get(title="Gallery: Batch of boxed units on a residential site")
        home.hero_image, home.hero_image_mobile = own, None
        home.hero_title_en = "Omar's headline"
        home.hero_alt_en = "Omar's alt"
        home.save()
        home.highlights.all().delete()
        HomeHighlight.objects.create(page=home, sort_order=0, title_en="Only one")
        self.apply()
        home = HomePage.objects.get()
        self.assertEqual(home.hero_image_id, own.pk)
        self.assertIsNone(home.hero_image_mobile_id)
        self.assertEqual((home.hero_title_en, home.hero_alt_en), ("Omar's headline", "Omar's alt"))
        self.assertEqual(home.highlights.count(), 1)


class RefinementTests(TestCase):
    """Refinement of navigation, brands, categories, gallery, services and the contractors panel."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def header(self, path="/"):
        return self.client.get(path).content.decode().split('<header id="site-header"')[1].split("</header>")[0]

    def test_navigation_uses_native_disclosure_menus(self):
        header = self.header("/products/wall/")
        self.assertEqual(header.count('<details class="nav-drop">'), 3)
        self.assertEqual(header.count("<summary>"), 3)
        self.assertIn('>Home</a>', header)
        self.assertIn('class="btn btn-accent btn-sm nav-quote" href="#contact"', header)
        self.assertIn('aria-controls="menu"', header)
        for href in ('"/#products"', '"/#brands"', '"/#install"', '"/#contractors"', '"/maintenance/"',
                     '"/duct-cleaning/"', '"/about/"', '"/contact/"', 'href="tel:', "https://wa.me/", 'hreflang="ar"'):
            self.assertIn(href, header)

    def test_every_internal_link_on_the_home_page_resolves(self):
        import re
        for prefix in ("", "/ar"):
            html = self.client.get(prefix + "/").content.decode()
            self.assertNotIn('href="#"', html)
            self.assertNotIn('href=""', html)
            ids = set(re.findall(r'id="([^"]+)"', html))
            for href in set(re.findall(r'href="([^"]+)"', html)):
                with self.subTest(href=href):
                    if href.startswith("#"):
                        self.assertIn(href[1:], ids)
                    elif href.startswith("/") and not href.startswith(("/static/", "/media/")):
                        path, _, anchor = href.partition("#")
                        self.assertEqual(self.client.get(path).status_code, 200)
                        if anchor and path in ("/", "/ar/"):
                            self.assertIn(anchor, ids)

    def test_brand_showcase_uses_brand_records_names_and_logo_slot(self):
        from wagtail.images.models import Image
        html = self.client.get("/").content.decode()
        wall = html.split('class="brand-wall"')[1].split("</ul>")[0]
        self.assertEqual(wall.count('class="brand-tile"'), Brand.objects.count())
        self.assertEqual(wall.count('class="brand-tile__mark"'), Brand.objects.count())
        self.assertNotIn("<img", wall)
        self.assertIn('href="/brands/daikin/"', wall)
        carrier = Brand.objects.get(slug="carrier")
        carrier.logo = Image.objects.first()
        carrier.save()
        wall = self.client.get("/").content.decode().split('class="brand-wall"')[1].split("</ul>")[0]
        self.assertEqual(wall.count("<img"), 1)
        self.assertIn('alt="Carrier"', wall)
        for banned in ("marquee", "authorised partner", "official partner"):
            self.assertNotIn(banned, wall)

    def test_services_link_only_to_things_that_exist(self):
        html = self.client.get("/ar/").content.decode()
        rows = html.split('class="service-rows"')[1].split("</ul>")[0]
        self.assertEqual(rows.count('class="service-row"'), 6)
        for href in ('href="#products"', 'href="#install"', 'href="/ar/maintenance/"', 'href="/ar/duct-cleaning/"',
                     'href="#contact"', 'href="#contractors"'):
            self.assertIn(href, rows)
        from core.models import HomeService
        HomeService.objects.filter(icon="parts").update(link_page=None, icon="")
        rows = self.client.get("/").content.decode().split('class="service-rows"')[1].split("</ul>")[0]
        self.assertEqual(rows.count("<a "), 5)      # a service with nowhere to go is plain text, not a dead link
        self.assertEqual(rows.count('<div class="service-row">'), 1)

    def test_contractors_panel_has_quote_and_boq_actions(self):
        html = self.client.get("/").content.decode()
        panel = html.split('id="contractors"')[1].split("</section>")[0]
        self.assertIn('href="#contact"', panel)
        self.assertIn("https://wa.me/971541981593?text=", panel)
        self.assertIn("Send your BOQ", panel)
        self.assertEqual(panel.count("<h3>"), 7)
        self.assertLess(panel.index("Project quotations"), panel.index("Warranty documentation"))
        self.assertIn('id="quote"', html)   # the existing quotation form the buttons lead to

    def test_gallery_leads_with_two_photos_and_holds_only_project_photos(self):
        from core.models import HomePage
        home = HomePage.objects.get()
        titles = [g.image.title for g in home.gallery.all()]
        self.assertEqual(titles[:2], ["Gallery: Two inverter condensers beside a villa",
                                      "Gallery: Crane lifting a package unit onto a roof"])
        self.assertEqual(len(titles), 8)
        self.assertTrue(all(t.startswith("Gallery: ") for t in titles))
        html = self.client.get("/").content.decode()
        gallery = html.split('id="gallery"')[1].split("</ul>")[0]
        self.assertEqual(gallery.count('class="is-lead"'), 2)
        self.assertEqual(gallery.count("data-lightbox"), 8)
        self.assertEqual(gallery.count('loading="lazy"'), 8)
        self.assertEqual(gallery.count("srcset="), 8)
        self.assertNotIn("hero-rooftop", gallery)
        self.assertIn('class="lightbox__count"', html)
        # Captions are the stored ones (the operator edits them in the admin).
        self.assertIn(home.gallery.first().caption_en, gallery)


class GalleryOrderMigrationTests(TestCase):
    """core 0008 reorders the gallery only while it is in its original order."""

    def apply(self):
        import importlib
        from django.apps import apps
        importlib.import_module("core.migrations.0008_gallery_lead_photos").apply_content(apps, None)

    def test_original_order_is_reordered_once_with_captions_intact(self):
        from core.models import HomePage
        call_command("seed_site", verbosity=0)
        home = HomePage.objects.get()
        before = {g.image.title: (g.caption_en, g.caption_ar, g.alt_en) for g in home.gallery.all()}
        self.apply()
        home = HomePage.objects.get()
        for obj in (home, home.get_latest_revision_as_object()):
            order = [g.image.title for g in obj.gallery.all()]
            self.assertEqual(order[:3], ["Gallery: Two inverter condensers beside a villa",
                                         "Gallery: Crane lifting a package unit onto a roof",
                                         "Gallery: Rooftop package units on a commercial building"])
        self.assertEqual({g.image.title: (g.caption_en, g.caption_ar, g.alt_en) for g in home.gallery.all()}, before)

    def test_an_edited_gallery_is_left_alone(self):
        from core.models import GalleryItem, HomePage
        call_command("seed_site", verbosity=0)
        home = HomePage.objects.get()
        last = home.gallery.order_by("-sort_order").first()
        GalleryItem.objects.filter(pk=last.pk).update(sort_order=-1)      # the operator moved a photo first
        order = list(GalleryItem.objects.filter(page=home).order_by("sort_order", "pk").values_list("pk", flat=True))
        self.apply()
        self.assertEqual(list(GalleryItem.objects.filter(page=home).order_by("sort_order", "pk")
                              .values_list("pk", flat=True)), order)


class DesignSystemTests(TestCase):
    """The stylesheets stay on the shared system: tokens, one type scale, six breakpoints."""

    def css(self, name):
        from django.conf import settings
        return (settings.BASE_DIR / "static/css" / name).read_text()

    def test_base_and_component_styles_use_tokens_only(self):
        import re
        for name in ("site.css", "additions.css", "components.css"):
            css = self.css(name)
            with self.subTest(file=name):
                self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b", css), [])          # colours come from tokens
                self.assertEqual(re.findall(r"font-size:\s*[\d.]+px", css), [])           # sizes come from the scale
        self.assertNotIn("linear-gradient(90deg,var(--sky),var(--cyan))",
                         self.css("components.css").split("System pass")[1])

    def test_only_six_breakpoints_are_used(self):
        import re
        found = set()
        for name in ("site.css", "additions.css", "components.css"):
            found |= set(re.findall(r"(?:max|min)-width:\s*(\d+)px", self.css(name)))
        self.assertLessEqual(found - {"399", "400", "641"}, {"480", "640", "860", "1024", "1180", "1380"})

    def test_type_scale_and_new_colour_tokens(self):
        import re
        tokens = self.css("tokens.css")
        for name in ("fs-display", "fs-h1", "fs-h2", "fs-h3", "fs-h4", "fs-h5", "fs-h6", "fs-lead", "fs-body",
                     "fs-ui", "fs-small", "fs-micro", "section-y", "card-pad", "grid-gap", "tap", "focus"):
            self.assertIn(f"--{name}:", tokens)
        tok = dict(re.findall(r"--([a-z0-9-]+):(#[0-9A-Fa-f]{6})", tokens))

        def lum(h):
            ch = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        def ratio(a, b):
            hi, lo = sorted((lum(tok[a]), lum(tok[b])), reverse=True)
            return (hi + 0.05) / (lo + 0.05)

        self.assertGreaterEqual(ratio("field-border", "white"), 3)       # form field outline (non-text, 3:1)
        self.assertGreaterEqual(ratio("navy", "sand-soft"), 4.5)         # notice text
        self.assertGreaterEqual(ratio("success", "success-bg"), 4.5)
        self.assertGreaterEqual(ratio("danger", "danger-bg"), 4.5)
        self.assertGreaterEqual(ratio("sky", "navy-800"), 4.5)           # text on raised navy surfaces
        self.assertGreaterEqual(ratio("cyan-ink", "white"), 4.5)         # focus ring and links on light

    def test_anchor_offset_follows_the_header_height(self):
        self.assertIn("scroll-padding-top:calc(var(--header-h)", self.css("site.css"))

    def test_internal_page_header_uses_the_accent_button_on_navy(self):
        call_command("seed_site", verbosity=0)
        html = self.client.get("/ar/products/vrf/").content.decode()
        hero = html.split('class="page-hero"')[1].split("</section>")[0]
        self.assertIn('class="btn btn-accent" href="#contact"', hero)
        self.assertNotIn("btn-primary", hero)
        self.assertIn('dir="ltr"', html.split('name="phone"')[1].split(">")[0])   # digits stay left-to-right


class FooterAndMotionTests(TestCase):
    """Footer built from CMS fields only, and motion that stays on the shared tokens."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def footer(self, path="/"):
        return self.client.get(path).content.decode().split("<footer")[1].split("</footer>")[0]

    def test_footer_contact_details_come_from_company_settings(self):
        from core.models import CompanySettings
        footer = self.footer()
        for text in ('href="tel:+971541981593"', "+971 54 198 1593", "https://wa.me/971541981593",
                     "mailto:info@opalgalaxy.ae", "Port Saeed", "Saturday – Thursday 8:00 – 18:00",
                     "img/opal-galaxy-logo-v1-reversed.svg", "opalgalaxy.ae"):
            self.assertIn(text, footer)
        self.assertEqual(footer.count('class="foot__ico"'), 5)
        cs = CompanySettings.load()
        cs.phone, cs.phone_display, cs.email, cs.address, cs.hours_short_en = "+97140000000", "+971 4 000 0000", "", "", ""
        cs.save()
        footer = self.footer()
        self.assertIn('href="tel:+97140000000"', footer)
        self.assertNotIn("mailto:", footer)                        # nothing is shown for an empty field
        self.assertEqual(footer.count('class="foot__ico"'), 2)

    def test_footer_links_exist_and_none_is_a_placeholder(self):
        import re
        for prefix in ("", "/ar"):
            footer = self.footer(prefix + "/products/vrf/")
            self.assertNotIn('href="#"', footer)
            self.assertNotIn('href=""', footer)
            for href in set(re.findall(r'href="(/[^"#]*)', footer)):
                if not href.startswith(("/static/", "/media/")):
                    with self.subTest(href=href):
                        self.assertEqual(self.client.get(href).status_code, 200)
            self.assertIn(f'href="{prefix}/privacy/"', footer)
            self.assertIn('hreflang="', footer)
        self.assertEqual(self.footer().count('<details class="foot__group'), 4)
        self.assertEqual(self.footer().count(" open>"), 4)        # open without JavaScript

    def test_social_buttons_are_links_only_when_a_url_is_set(self):
        from core.models import CompanySettings
        social = self.footer().split('class="social"')[1].split("</ul>")[0]
        self.assertEqual((social.count("<a "), social.count("<span")), (0, 4))
        cs = CompanySettings.load()
        cs.facebook_url, cs.tiktok_url = "https://www.facebook.com/example", "https://www.tiktok.com/@example"
        cs.save()
        social = self.footer().split('class="social"')[1].split("</ul>")[0]
        self.assertEqual((social.count("<a "), social.count("<span")), (2, 2))
        self.assertIn('aria-label="Facebook"', social)

    def test_motion_uses_tokens_and_respects_reduced_motion(self):
        import re
        from django.conf import settings
        css = (settings.BASE_DIR / "static/css/components.css").read_text()
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        tokens = (settings.BASE_DIR / "static/css/tokens.css").read_text()
        # Durations are the three tokens; the only literals are zero and the reduced-motion override.
        literals = set(re.findall(r"(?<![\w.-])(\d*\.?\d+m?s)\b", css))
        self.assertLessEqual(literals, {"0s", ".001ms"})
        for name in ("t-fast", "t", "t-slow", "stagger", "lift", "zoom", "reveal-y"):
            self.assertIn(f"--{name}:", tokens)
        self.assertIn("--t-fast:0s;--t:0s;--t-slow:0s;--stagger:0s;--lift:0px;--zoom:1;--reveal-y:0px", tokens)
        self.assertIn("@media (prefers-reduced-motion:reduce){", css)
        self.assertIn("animation-duration:.001ms!important", css)
        for banned in ("infinite", "marquee", "parallax", "background-attachment:fixed"):
            self.assertNotIn(banned, css)
        self.assertIn(".social a:hover,.social a:focus-visible{", css)

    def test_reveal_never_hides_content_without_javascript(self):
        import re
        from django.conf import settings
        css = (settings.BASE_DIR / "static/css/components.css").read_text()
        for rule in re.findall(r"([^{}]*\[data-reveal\][^{}]*)\{[^}]*opacity:0", css):
            self.assertIn(".js ", rule)     # hidden only when the script has marked the page
        hero = self.client.get("/").content.decode().split('class="hero-x"')[1].split("</section>")[0]
        self.assertNotIn("data-reveal", hero)
