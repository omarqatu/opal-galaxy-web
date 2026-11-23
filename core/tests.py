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
        self.assertContains(en, "<h1>Engineered Cooling. Delivered with Confidence.</h1>", html=True)
        self.assertContains(en, "Explore HVAC Solutions")
        self.assertContains(en, "Request a Project Quote")
        self.assertContains(ar, "تكييف بمعايير هندسية، وتنفيذ جدير بالثقة")
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
        grid = html.split("cat-grid")[1].split("</section>")[0]
        self.assertEqual(grid.count('class="card cat-card"'), ProductCategory.objects.live().count())
        self.assertNotIn("<img", grid)
        self.assertIn("<svg", grid)
        self.assertIn("وحدات شباك", grid)

    def test_services_process_and_duct_cleaning(self):
        en, ar = self.client.get("/").content.decode(), self.client.get("/ar/").content.decode()
        for title in ("HVAC supply", "Installation", "Maintenance and spare parts", "AC duct cleaning",
                      "Project quotations", "Contractor and commercial project support",
                      "Project consultation and site assessment", "Equipment supply and installation",
                      "Testing, commissioning and handover", "BOQ support", "Warranty documentation"):
            self.assertIn(title, en)
        self.assertIn("تنظيف مجاري التكييف", ar)
        self.assertIn('href="/maintenance/"', en.split('id="services"')[1].split("</section>")[0])
        # The duct cleaning page does not exist yet: the button leads to the quote form.
        self.assertIn('href="#contact">Ask about duct cleaning', en)

    def test_unverified_claims_are_not_headlines(self):
        html = self.client.get("/").content.decode()
        self.assertNotIn('class="facts"', html)
        self.assertNotIn("<h3>Volume quote within one working day</h3>", html)
        self.assertIn("Delivery within 48 hours", html)  # kept, as a quiet note under the hero

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
        self.assertContains(self.client.get("/"), '<span class="alt">We never share your details.</span>')
        HomePage.objects.get().add_child(instance=ServicePage(title="Privacy", slug="privacy", title_en="Privacy"))
        self.assertContains(self.client.get("/"), '<a href="/privacy/">We never share your details.</a>')
        self.assertContains(self.client.get("/ar/"), 'href="/ar/privacy/"')

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
        menu = html.split('id="menu"')[1].split("</ul>")[0]
        for href in ('/#products"', '/#brands"', '/#contractors"', '/#install"', '"/maintenance/"', '"#contact"'):
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
