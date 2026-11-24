from django.core.management import call_command
from django.test import TestCase, override_settings

from catalog.models import Brand, ProductCategory, Supply
from core.models import QuoteRequest


def approve_gallery():
    """What Omar does in the admin: approve the photos and mark them for the homepage in their order."""
    from django.db.models import F
    from core.models import FieldPhoto
    FieldPhoto.objects.exclude(sort_order=None).update(approved_for_publication=True, show_on_homepage=True,
                                                       home_order=F("sort_order") + 1)
    FieldPhoto.objects.filter(sort_order=None).update(approved_for_publication=True)


def field_photos():
    from core.models import FieldPhoto
    return list(FieldPhoto.objects.all())


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
        approve_gallery()
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
        for href in ('/#products"', '/#brands"', '/#contractors"', '/#install"', '"/maintenance/"',
                     '"/duct-cleaning/"', '"/contact/"'):
            self.assertIn(href, menu)
        # Home is reached through the logo and About through the footer (Task 17-C).
        self.assertIn('<a class="logo" href="/"', html)
        self.assertNotIn('"/about/"', menu)
        self.assertIn('href="/about/"', html.split("<footer")[1])

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
        gallery_before = [(p.image_id, p.title_en) for p in field_photos()]
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
        self.assertEqual([(p.image_id, p.title_en) for p in field_photos()], gallery_before)
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
        import re
        body = en.split('id="app"')[1].split('id="contact"')[0]
        visible = re.sub(r"<[^>]+>", " ", body)        # what a visitor reads; link addresses are URL-encoded and hold "%"
        for banned in ("AED", "hours", "guarantee", "certified", "warranty", "%"):
            self.assertNotIn(banned, visible)

    def test_duct_cleaning_request_is_saved_with_its_service(self):
        self.client.post("/quote/", {"phone": "+971501234567", "unit": "duct-cleaning",
                                     "source_page": "/duct-cleaning/"})
        self.assertEqual(QuoteRequest.objects.get().product, "duct-cleaning")

    def test_faq_page_shows_every_question_even_when_not_featured(self):
        from core.models import FaqItem
        FaqItem.objects.update(featured=False)
        html = self.client.get("/ar/faq/").content.decode()
        self.assertEqual(html.split('class="faq-list"')[1].split("</section>")[0].count('<article class="faq-item">'), 6)
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

    def test_category_page_has_no_counts_and_keeps_data_left_to_right(self):
        en = self.client.get("/products/wall/").content.decode()
        ar = self.client.get("/ar/products/wall/").content.decode()
        for html in (en, ar):
            self.assertNotIn("Available from <b>", html)
            self.assertNotIn("علامات تجارية</span>", html)
        self.assertIn('<div class="tech__data" dir="ltr" lang="en">', ar)
        self.assertNotIn("wall mounted split", en)   # the old lower-cased button text
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
        approve_gallery()
        from core.models import HomePage
        home = HomePage.objects.get()
        self.assertNotIn(home.hero_image_id, [p.image_id for p in field_photos()])
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
        self.assertNotIn('>Home</a>', header)                     # the logo is the link to the home page
        self.assertIn('<a class="logo" href="/"', header)
        self.assertIn('class="btn btn-accent btn-sm nav-quote" href="#contact"', header)
        self.assertIn('aria-controls="menu"', header)
        for href in ('"/#products"', '"/#brands"', '"/#install"', '"/#contractors"', '"/maintenance/"',
                     '"/duct-cleaning/"', '"/contact/"', 'href="tel:', "https://wa.me/", 'hreflang="ar"'):
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
        approve_gallery()
        from core.models import HomePage
        home = HomePage.objects.get()
        titles = [g.image.title for g in field_photos()]
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
        self.assertIn(field_photos()[0].title_en, gallery)


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


class PremiumInternalPagesTests(TestCase):
    """Reference designs for the brand and category templates (Carrier, VRF systems)."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def test_every_brand_and_category_page_uses_the_premium_templates(self):
        import os, re
        from django.conf import settings
        self.assertFalse(os.path.exists(settings.BASE_DIR / "templates/catalog/brand_premium.html"))
        self.assertFalse(os.path.exists(settings.BASE_DIR / "templates/includes/supply_row.html"))
        pages = [(f"/brands/{b.slug}/", b.live_supplies().count()) for b in Brand.objects.all()]
        pages += [(f"/products/{c.slug}/", c.supplies.count()) for c in ProductCategory.objects.live()]
        self.assertGreaterEqual(len(pages), 20)
        for path, rows in pages:
            for prefix, direction in (("", "ltr"), ("/ar", "rtl")):
                with self.subTest(path=prefix + path):
                    response = self.client.get(prefix + path)
                    self.assertEqual(response.status_code, 200)
                    html = response.content.decode()
                    self.assertIn(f'dir="{direction}"', html.split("<head>")[0])
                    self.assertEqual(html.count("<h1"), 1)
                    self.assertEqual(html.count('<details class="tech"'), rows)       # one panel per catalogue row
                    self.assertEqual(html.count('class="tech__data" dir="ltr" lang="en"'), rows)
                    self.assertEqual('class="empty-state"' in html, rows == 0 and path.startswith("/brands/"))
                    self.assertIn('id="quote"', html)
                    self.assertIn('class="cta-band"', html)
                    self.assertNotIn('href="#"', html)
                    self.assertNotIn("supply-row", html)
                    self.assertNotIn("product types", html)
                    ids = set(re.findall(r'id="([^"]+)"', html))
                    for anchor in set(re.findall(r'href="#([^"]+)"', html)):
                        self.assertIn(anchor, ids)

    def test_every_catalogue_row_is_shown_verbatim_on_both_of_its_pages(self):
        import re
        from core.templatetags.opal import model_groups
        norm = lambda t: re.sub(r"\s+", " ", t)
        cache = {}
        for row in Supply.objects.filter(category__live=True).select_related("brand", "category"):
            for path in (f"/brands/{row.brand.slug}/", f"/ar/products/{row.category.slug}/"):
                if path not in cache:
                    cache[path] = self.text_of(self.client.get(path).content.decode())
                with self.subTest(row=f"{row.brand.slug}/{row.category.slug}", path=path):
                    # the items of a row, joined again with the catalogue separator, give back the stored models
                    rebuilt = norm(" · ".join(item for _l, items in model_groups(row) for item in items))
                    for item in (i for _l, items in model_groups(row) for i in items):
                        self.assertIn(norm(item), cache[path])
                    stored = norm(row.models_text)
                    for piece in rebuilt.split(" · "):
                        self.assertIn(piece, stored)
                    if not row.pending:
                        for line in row.spec_list():
                            self.assertIn(norm(line), cache[path])

    def test_fragments_that_continue_an_item_stay_with_it(self):
        from core.templatetags.opal import mark_ids, model_groups
        g = lambda text: model_groups(Supply(models_text=text))
        self.assertEqual(g("High Ambient Desert Master: 50ZPM 36 · 48 · 60 · 50TCM A07 · D08 · D09 · 50TJM 18 · 22"),
                         [("High Ambient Desert Master", ["50ZPM 36 · 48 · 60", "50TCM A07 · D08 · D09", "50TJM 18 · 22"])])
        self.assertEqual(g("Split 18,000 · 24,000 · 30,000 · 36,000 BTU"), [("", ["Split 18,000 · 24,000 · 30,000 · 36,000 BTU"])])
        self.assertEqual(g("Inverter: SGCA 3600i · 4800i (cool & heat) · Fixed speed: SGCA-HE (SGCA3600HE)"),
                         [("Inverter", ["SGCA 3600i · 4800i (cool & heat)"]), ("Fixed speed", ["SGCA-HE (SGCA3600HE)"])])
        self.assertEqual(g("side discharge 38VS007168HCMM · 38VS008168HCMM · 39HQM"),      # full identifiers stay separate
                         [("", ["side discharge 38VS007168HCMM", "38VS008168HCMM", "39HQM"])])
        self.assertEqual(g("IVCF Series"), [("", ["IVCF Series"])])
        self.assertEqual(g(""), [])
        for refrigerant in ("R410A", "R-410A", "R407C", "R-134A", "R32", "R22"):
            self.assertNotIn("tech__id", mark_ids(f"scroll {refrigerant} unit"))
        self.assertIn("tech__id", mark_ids("ASGA 18 – 36 FUTD / R410A 38QHA/42QHA"))

    def test_admin_preview_of_a_category_renders_with_the_new_template(self):
        category = ProductCategory.objects.get(slug="ducted")
        for mode, direction in (("en", "ltr"), ("ar", "rtl")):
            response = category.make_preview_request(preview_mode=mode)
            self.assertEqual(response.status_code, 200)
            html = response.content.decode()
            self.assertIn(f'dir="{direction}"', html.split("<head>")[0])
            self.assertEqual(html.count('<details class="tech"'), category.supplies.count())

    @staticmethod
    def text_of(markup):
        """What a reader (or a screen reader) gets: the markup with every tag removed."""
        import html as htmllib, re
        return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", "", markup)))

    def test_catalogue_text_is_printed_verbatim_in_both_languages(self):
        import re
        for path, rows in (("/brands/carrier/", Supply.objects.filter(brand__slug="carrier", category__live=True)),
                           ("/ar/products/vrf/", Supply.objects.filter(category__slug="vrf"))):
            html = self.client.get(path).content.decode()
            page = self.text_of(html)
            from core.templatetags.opal import model_groups
            for row in rows:
                for _label, items in model_groups(row):
                    for item in items:
                        self.assertIn(re.sub(r"\s+", " ", item), page)
                if not row.pending:
                    for line in row.spec_list():
                        self.assertIn(re.sub(r"\s+", " ", line), page)       # separators included
            # each specification row, tags removed, is exactly one stored line
            stored = {re.sub(r"\s+", " ", l) for r in rows if not r.pending for l in r.spec_list()}
            shown = [self.text_of(li).strip() for ul in re.findall(r'<ul class="tech__specs"[^>]*>(.*?)</ul>', html, re.S)
                     for li in re.findall(r"<li[^>]*>(.*?)</li>", ul, re.S)]
            self.assertTrue(shown)
            self.assertLessEqual(set(shown), stored)
        self.assertIn('<div class="tech__data" dir="ltr" lang="en">', self.client.get("/ar/products/vrf/").content.decode())

    def test_identifier_and_separator_styling_changes_no_character(self):
        from core.templatetags.opal import mark_ids, spec_parts
        samples = ["XPower 38VT008168HTMM – 38VT020168HTMM (8 – 20 HP, single module)",
                   "4-way cassette 40VU___S-4S-TEE1", "Optimax™ Pro 38KHCT/42KHCT", "50TCM A07", "IVCF Series",
                   "AquaForce® 30XA", "SGS 181i5", "A <b> & C"]
        for text in samples:
            self.assertEqual(self.text_of(str(mark_ids(text))), text)
        self.assertIn('<b class="tech__id">38VT008168HTMM</b>', mark_ids(samples[0]))
        self.assertIn('<b class="tech__id">40VU___S-4S-TEE1</b>', mark_ids(samples[1]))
        self.assertIn('<b class="tech__id">38KHCT/42KHCT</b>', mark_ids(samples[2]))
        self.assertNotIn("tech__id", mark_ids("IVCF Series"))        # a name, not an identifier
        self.assertNotIn("tech__id", mark_ids("8 – 20 HP"))           # a figure, not an identifier
        self.assertIn("&lt;b&gt; &amp; C", mark_ids("A <b> & C"))
        line = "Refrigerant R410A · heat pump · 380-415/3/50"
        self.assertEqual(" · ".join(spec_parts(line)), line)

    def test_model_groups_only_split_at_the_catalogue_separators(self):
        from core.templatetags.opal import model_groups, spec_rows
        row = Supply(models_text="Outdoor: XPower 38VT008 – 38VT020 (8 – 20 HP) · side discharge 38VS007 · "
                                 "Indoor: 4-way cassette 40VU___S-4S-TEE1 · concealed duct 40VD007S",
                     specs="XPower 38VT: cooling 22.4 – 56.0 kW (76,000 – 190,000 Btu/h) per module\nRefrigerant R410A")
        self.assertEqual(model_groups(row), [
            ("Outdoor", ["XPower 38VT008 – 38VT020 (8 – 20 HP)", "side discharge 38VS007"]),
            ("Indoor", ["4-way cassette 40VU___S-4S-TEE1", "concealed duct 40VD007S"])])
        chillers = Supply(models_text="Air cooled: AquaForce® 30XA · AquaSnap® 30RB. Water cooled: AquaEdge® 19MV · "
                                      "Global Chiller 30HXC. AHU: Airovision™ 39HQ")
        self.assertEqual([g[0] for g in model_groups(chillers)], ["Air cooled", "Water cooled", "AHU"])
        self.assertEqual(model_groups(Supply(models_text="IVCF Series")), [("", ["IVCF Series"])])
        for every in (row, chillers):       # nothing is added: every item is a slice of the stored text
            for _label, items in model_groups(every):
                for item in items:
                    self.assertIn(item, every.models_text)
        self.assertEqual([r["btu"] for r in spec_rows(row)], [True, False])   # flagged, not converted
        self.assertEqual([r["text"] for r in spec_rows(row)], row.spec_list())

    def test_vrf_page_derives_nothing_from_hp(self):
        import re
        page = self.client.get("/products/vrf/").content.decode()
        stored = " ".join(s.specs + " " + s.models_text for s in Supply.objects.filter(category__slug="vrf"))
        stored += " " + " ".join(ProductCategory.objects.values_list("capacity_range", flat=True))
        body = page.split('id="app"')[1].split('id="contact"')[0]
        for figure in set(re.findall(r"[\\d,]{4,}\\s*(?:BTU|Btu)[/\\w]*", body)):
            self.assertIn(figure, stored)     # every BTU figure on the page is one the catalogue states

    def test_brand_without_rows_gets_an_empty_state_not_invented_content(self):
        page = self.client.get("/brands/lg/").content.decode()
        self.assertIn('class="empty-state"', page)
        self.assertIn("Models and capacities are confirmed on the quote.", page)
        self.assertNotIn('class="tech"', page)
        self.assertNotIn("cat-index", page)

    def test_draft_copy_is_only_for_signed_in_reviewers_and_is_never_saved(self):
        from django.contrib.auth import get_user_model
        from django.test import override_settings
        from catalog import preview
        before = (Brand.objects.get(slug="carrier").about_en, Brand.objects.get(slug="carrier").line_ar,
                  ProductCategory.objects.get(slug="vrf").lead_en)
        draft_en = preview.DEMO[("brand", "carrier")]["intro"]["en"]
        draft_ar = preview.DEMO[("category", "vrf")]["intro"]["ar"]
        url = "/brands/carrier/?draft=1"
        # the public, on staging or anywhere else: the normal page
        for noindex in (True, False):
            with override_settings(SITE_NOINDEX=noindex):
                page = self.client.get(url)
                self.assertNotContains(page, draft_en)
                self.assertNotContains(page, "draft-banner")
                self.assertContains(page, before[0][:60])
                self.assertNotIn("no-store", page.headers.get("Cache-Control", ""))
        # a signed-in visitor without admin access: still the normal page
        User = get_user_model()
        self.client.force_login(User.objects.create_user("visitor", "v@example.com", "pw"))
        self.assertNotContains(self.client.get(url), draft_en)
        # a reviewer (Wagtail admin access): the draft, marked, uncached
        self.client.force_login(User.objects.create_superuser("omar", "o@example.com", "pw"))
        page = self.client.get(url)
        self.assertContains(page, draft_en)
        self.assertContains(page, 'class="draft-banner"')
        self.assertContains(page, "is-draft")
        self.assertEqual(page.headers["Cache-Control"], "private, no-store")
        self.assertContains(self.client.get("/ar/products/vrf/?draft=1"), draft_ar)
        self.assertNotContains(self.client.get("/brands/carrier/"), draft_en)        # only on request
        self.assertNotContains(self.client.get("/brands/midea/?draft=1"), "draft-banner")
        self.client.logout()
        with override_settings(DEBUG=True):                                          # local development
            self.assertContains(self.client.get(url), draft_en)
        self.assertEqual(before, (Brand.objects.get(slug="carrier").about_en, Brand.objects.get(slug="carrier").line_ar,
                                  ProductCategory.objects.get(slug="vrf").lead_en))

    def test_quotation_band_keeps_the_general_site_texts(self):
        from django.contrib.auth import get_user_model
        from catalog import preview
        for page in preview.DEMO.values():
            self.assertNotIn("cta_title", page)
            self.assertNotIn("cta_text", page)
        self.client.force_login(get_user_model().objects.create_superuser("rev", "r@example.com", "pw"))
        for url in ("/brands/carrier/?draft=1", "/products/vrf/?draft=1"):
            band = self.client.get(url).content.decode().split('class="cta-band"')[1].split("</section>")[0]
            self.assertIn("Request a project quote", band)
            self.assertNotIn("is-draft", band)

    def test_draft_copy_states_no_specification_or_commercial_claim(self):
        import re
        from catalog import preview
        for page in preview.DEMO.values():
            for texts in page.values():
                for text in texts.values():
                    self.assertIsNone(re.search(r"\\d", text), text)   # no figure of any kind
                    for banned in ("authoris", "authoriz", "warranty", "certif", "in stock", "delivery", "price",
                                   "معتمد", "ضمان", "شهادة", "مخزون", "توصيل", "أسعار"):
                        self.assertNotIn(banned, text.lower())

    def test_reference_pages_keep_routes_links_and_quote_form(self):
        import re
        for path in ("/brands/carrier/", "/ar/products/vrf/"):
            page = self.client.get(path).content.decode()
            self.assertEqual(page.count("<h1"), 1)
            self.assertIn('id="quote"', page)
            self.assertNotIn('href="#"', page)
            ids = set(re.findall(r'id="([^"]+)"', page))
            for anchor in set(re.findall(r'href="#([^"]+)"', page)):
                self.assertIn(anchor, ids)
        vrf = self.client.get("/products/vrf/").content.decode()
        self.assertIn('href="#brand-carrier"', vrf)
        self.assertIn('id="brand-carrier"', vrf)
        self.assertNotIn(" ton", vrf.split('class="cat-cards"')[1].split("</ul>")[0])


class FieldGalleryPageTests(TestCase):
    """PR B of the field gallery: the public page, its filter, the viewer markup, links and media rules."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def home(self):
        from core.models import HomePage
        return HomePage.objects.get()

    def make_page(self, publish=True):
        """What Omar does in the admin: add a content page of kind "gallery" under the home page."""
        from core.models import ContentPage
        page = ContentPage(title="Gallery", slug="gallery", kind="gallery", title_en="Field gallery",
                           title_ar="معرض الصور الميدانية", live=False)
        self.home().add_child(instance=page)
        if publish:
            page.save_revision().publish()
        return page

    def categories(self):
        from core.models import GalleryCategory
        return [GalleryCategory.objects.create(name_en=n, name_ar=a, slug=sl, sort_order=i) for i, (n, a, sl) in enumerate([
            ("AC Duct Cleaning", "تنظيف مجاري التكييف", "duct-cleaning"),
            ("Field Operations", "العمليات الميدانية", "field-operations"),
            ("Maintenance", "الصيانة", "maintenance")])]

    def wall(self, url="/gallery/"):
        html = self.client.get(url).content.decode()
        return html.split('id="gallery"')[1].split("</ul>")[0] if 'id="gallery"' in html else ""

    def test_nothing_is_public_until_the_page_is_created_and_published(self):
        from core.models import ContentPage
        approve_gallery()
        self.assertFalse(ContentPage.objects.filter(kind="gallery").exists())     # no migration creates it
        self.assertEqual(self.client.get("/gallery/").status_code, 404)
        self.make_page(publish=False)                                              # Omar's draft
        for path in ("/gallery/", "/ar/gallery/"):
            self.assertEqual(self.client.get(path).status_code, 404)
        for path in ("/", "/ar/", "/about/"):
            html = self.client.get(path).content.decode()
            self.assertNotIn("/gallery/", html)
            self.assertNotIn("View full gallery", html)
        self.assertNotIn("/gallery/", self.client.get("/sitemap.xml").content.decode())

    def test_published_page_adds_the_links_in_both_languages(self):
        approve_gallery()
        self.make_page()
        en, ar = self.client.get("/").content.decode(), self.client.get("/ar/").content.decode()
        self.assertIn('<a class="link-arrow" href="/gallery/">View full gallery', en)
        self.assertIn('<a class="link-arrow" href="/ar/gallery/">عرض المعرض كاملاً', ar)
        # Header: a direct Media link just before Contact, no About item; footer: About and Media in the Company column.
        header = en.split("<header")[1].split("</header>")[0]
        self.assertIn('<li><a href="/gallery/">Media</a></li>', header)
        self.assertEqual(header.count('href="/gallery/"'), 1)
        self.assertNotIn('href="/about/"', header)
        self.assertLess(header.index('href="/#contractors"'), header.index('href="/gallery/"'))
        self.assertLess(header.index('href="/gallery/"'), header.index('href="/contact/"'))
        self.assertEqual(header.count("nav-drop"), 3)
        footer = en.split('<footer')[1]
        self.assertIn('<a href="/gallery/">Media</a>', footer)
        self.assertIn('href="/about/"', footer)
        self.assertIn('<li><a href="/ar/gallery/">الوسائط</a></li>', ar.split("<header")[1].split("</header>")[0])
        self.assertIn('<a href="/gallery/" aria-current="page">Media</a>',
                      self.client.get("/gallery/").content.decode().split("<header")[1].split("</header>")[0])
        self.assertIn("/gallery/", self.client.get("/sitemap.xml").content.decode())
        self.assertEqual(self.client.get("/gallery/").status_code, 200)
        page = self.client.get("/ar/gallery/")
        self.assertEqual(page.status_code, 200)
        self.assertIn('dir="rtl"', page.content.decode())
        self.assertIn("معرض الصور الميدانية", page.content.decode())

    def test_header_order_is_products_brands_services_contractors_media_contact(self):
        import re
        self.make_page()
        for path, labels in (("/", ["Products", "Brands", "Services", "Contractors", "Media", "Contact"]),
                             ("/ar/", None)):
            header = self.client.get(path).content.decode().split("<header")[1].split("</header>")[0]
            menu = header.split('id="menu"')[1].split('class="menu__foot"')[0]
            top = re.findall(r'^      <li[^>]*>(?:<details class="nav-drop"><summary>|<a [^>]*>)([^<{]+)', menu, re.M)
            self.assertEqual(len(top), 6, top)
            if labels:
                self.assertEqual([t.strip() for t in top], labels)
            else:
                self.assertEqual(top[4].strip(), "الوسائط")
            # the actions next to the menu are all still there
            for needle in ('class="lang"', 'tool-btn--call', 'tool-btn--wa', 'nav-quote', 'id="burger"', 'class="logo"'):
                self.assertIn(needle, header)

    def test_without_a_gallery_page_the_header_has_no_media_or_about_item(self):
        html = self.client.get("/").content.decode()
        header = html.split("<header")[1].split("</header>")[0]
        self.assertNotIn("Media", header)
        self.assertNotIn('href="/about/"', header)
        self.assertEqual(header.count("nav-drop"), 3)
        self.assertIn('href="/about/"', html.split("<footer")[1])       # About stays reachable from the footer

    def test_only_approved_photos_are_shown(self):
        from core.models import FieldPhoto
        self.make_page()
        self.assertEqual(self.wall(), "")                           # nothing approved: no grid, no viewer
        html = self.client.get("/gallery/").content.decode()
        self.assertNotIn('id="lightbox"', html)
        items = field_photos()
        for g in items[:5]:
            g.approved_for_publication = True
            g.save()
        wall = self.wall()
        self.assertEqual(wall.count("data-lightbox"), 5)
        for g in items[:5]:
            self.assertIn(g.alt_en, wall)
        for g in items[5:]:
            self.assertNotIn(g.alt_en, wall)
            self.assertNotIn(g.image.file.name.split("/")[-1].rsplit(".", 1)[0] + ".", wall)
        FieldPhoto.objects.filter(pk=items[0].pk).update(approved_for_publication=False)
        self.assertNotIn(items[0].alt_en, self.wall())
        arabic = self.wall("/ar/gallery/")
        self.assertEqual(arabic.count("data-lightbox"), 4)
        self.assertIn(items[1].alt_ar, arabic)
        self.assertIn(items[1].caption_ar, arabic)

    def test_category_filter_lists_only_categories_with_approved_photos(self):
        from core.models import FieldPhoto
        self.make_page()
        duct, field, maintenance = self.categories()
        items = field_photos()
        FieldPhoto.objects.filter(pk__in=[items[0].pk, items[1].pk]).update(category=field, approved_for_publication=True)
        FieldPhoto.objects.filter(pk=items[2].pk).update(category=maintenance, approved_for_publication=True)
        FieldPhoto.objects.filter(pk=items[3].pk).update(category=duct)                    # not approved
        FieldPhoto.objects.filter(pk=items[4].pk).update(approved_for_publication=True)   # approved, no category
        html = self.client.get("/gallery/").content.decode()
        nav = html.split('class="gallery-filter"')[1].split("</nav>")[0]
        self.assertIn('aria-current="true">All photos', nav)
        self.assertIn('href="?category=field-operations#photos"', nav)
        self.assertIn('href="?category=maintenance#photos"', nav)
        self.assertNotIn("duct-cleaning", nav)                     # empty for visitors: hidden
        self.assertLess(nav.index("Field Operations"), nav.index("Maintenance"))
        self.assertEqual(self.wall().count("data-lightbox"), 4)
        only = self.wall("/gallery/?category=field-operations")
        self.assertEqual(only.count("data-lightbox"), 2)
        self.assertIn(items[0].alt_en, only)
        self.assertNotIn(items[2].alt_en, only)
        active = self.client.get("/gallery/?category=field-operations").content.decode()
        self.assertIn('aria-current="true">Field Operations', active)
        # A hidden or unknown category shows every approved photo instead of an error or an unapproved one.
        for slug in ("duct-cleaning", "nope"):
            fallback = self.client.get(f"/gallery/?category={slug}")
            self.assertEqual(fallback.status_code, 200)
            self.assertEqual(self.wall(f"/gallery/?category={slug}").count("data-lightbox"), 4)
            self.assertNotIn(items[3].alt_en, fallback.content.decode())
        self.assertIn("العمليات الميدانية", self.client.get("/ar/gallery/").content.decode())

    def test_no_filter_is_shown_without_categories(self):
        approve_gallery()
        self.make_page()
        self.assertNotIn("gallery-filter", self.client.get("/gallery/").content.decode())

    def test_at_most_two_featured_photos_lead_and_the_grid_stays_balanced(self):
        from core.models import FieldPhoto
        approve_gallery()
        self.make_page()
        items = field_photos()
        order = lambda: [a.split('"')[0] for a in self.wall().split('alt="')[1:]]
        self.assertEqual(self.wall().count('class="is-lead"'), 0)                 # none featured: uniform grid
        self.assertEqual(order(), [g.alt_en for g in items])                       # the editor's order
        FieldPhoto.objects.filter(pk=items[4].pk).update(featured=True)           # one featured: paired with the next photo
        self.assertEqual(self.wall().count('class="is-lead"'), 2)
        self.assertEqual(order()[:3], [items[4].alt_en, items[0].alt_en, items[1].alt_en])
        FieldPhoto.objects.filter(pk__in=[items[2].pk, items[6].pk]).update(featured=True)   # three featured: two lead
        self.assertEqual(self.wall().count('class="is-lead"'), 2)
        self.assertEqual(order()[:4], [items[2].alt_en, items[4].alt_en, items[0].alt_en, items[1].alt_en])
        self.assertEqual(len(order()), 8)
        FieldPhoto.objects.exclude(pk=items[4].pk).update(approved_for_publication=False)    # a single photo
        self.assertEqual(self.wall().count("data-lightbox"), 1)

    def test_images_are_responsive_webp_renditions_and_never_enlarged(self):
        import re
        from wagtail.images.models import Rendition
        approve_gallery()
        self.make_page()
        wall = self.wall()
        self.assertEqual(wall.count("srcset="), 8)
        self.assertEqual(wall.count("sizes="), 8)
        self.assertEqual(wall.count('loading="lazy"'), 6)          # the first two load at once
        self.assertEqual(len(re.findall(r'width="\d+" height="\d+"', wall)), 8)
        urls = set(re.findall(r"/media/[^\s\",]+", wall))
        self.assertTrue(urls)
        for url in urls:
            self.assertTrue(url.startswith("/media/images/") and url.endswith(".webp"), url)   # never the original file
        widest = max(g.image.width for g in field_photos())
        for width in re.findall(r" (\d+)w", wall):
            self.assertLessEqual(int(width), widest)
        for rendition in Rendition.objects.filter(image__in=[g.image for g in field_photos()]):
            self.assertLessEqual(rendition.width, rendition.image.width)
        self.assertIn('id="lightbox"', self.client.get("/gallery/").content.decode())
        self.assertIn('aria-label="Close"', self.client.get("/gallery/").content.decode())

    def test_only_gallery_records_are_shown_never_the_illustration(self):
        approve_gallery()
        self.make_page()
        home = self.home()
        html = self.client.get("/gallery/").content.decode()
        for image in (home.hero_image, home.hero_image_mobile):
            if image:
                self.assertNotIn(image.file.name.split("/")[-1].rsplit(".", 1)[0], html)

    def test_pages_are_revalidated_so_a_withdrawn_photo_does_not_linger(self):
        approve_gallery()
        self.make_page()
        self.assertEqual(self.client.get("/gallery/")["Cache-Control"], "no-cache")
        self.assertEqual(self.client.get("/")["Cache-Control"], "no-cache")

    def test_admin_preview_of_the_draft_page_shows_the_gallery(self):
        approve_gallery()
        page = self.make_page(publish=False)
        response = page.make_preview_request()
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="gallery"', response.content.decode())


class MediaFilesTests(TestCase):
    """Uploaded files: originals are not public, renditions carry no position data and a bounded cache lifetime."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def photo_with_gps(self):
        import io
        from django.core.files.base import ContentFile
        from PIL import Image as PILImage
        from wagtail.images.models import Image
        exif = PILImage.Exif()
        exif[0x010F] = "TestCam"
        exif[0x8825] = {1: "N", 2: (25.0, 15.0, 0.0), 3: "E", 4: (55.0, 18.0, 0.0)}
        data = io.BytesIO()
        PILImage.new("RGB", (1200, 1600), (90, 120, 150)).save(data, "JPEG", exif=exif)
        image = Image(title="GPS probe", file=ContentFile(data.getvalue(), "gps-probe.jpg"))
        image.save()
        self.addCleanup(lambda: [r.file.delete(False) for r in image.renditions.all()] and None)
        self.addCleanup(lambda: image.file.delete(False))
        return image

    def test_renditions_carry_no_exif_or_gps_but_the_original_does(self):
        from PIL import Image as PILImage
        from core.templatetags.opal import photo
        image = self.photo_with_gps()
        self.assertTrue(PILImage.open(image.file.path).getexif().get_ifd(0x8825))     # the upload is kept as it is
        sizes = photo(image, "320 480 720 960 2400")
        files = [image.get_rendition("max-1600x1600|format-webp")] + list(image.renditions.all())
        self.assertGreaterEqual(len(files), 5)
        for rendition in files:
            opened = PILImage.open(rendition.file.path)
            self.assertEqual(opened.format, "WEBP")
            self.assertEqual(len(opened.getexif()), 0)
            self.assertFalse(opened.getexif().get_ifd(0x8825))
        self.assertTrue(sizes["srcset"].endswith(" 1200w"))        # 2400 is not produced: no upscaling
        self.assertEqual(sizes["srcset"].count(".webp"), 5)       # 320, 480, 720, 960 and the original 1200, once each

    def test_original_uploads_are_served_to_signed_in_admin_users_only(self):
        from django.contrib.auth import get_user_model
        image = self.photo_with_gps()
        url = "/media/" + image.file.name
        self.assertTrue(url.startswith("/media/original_images/"))
        self.assertEqual(self.client.get(url).status_code, 404)
        get_user_model().objects.create_user("visitor", password="pw")
        self.client.login(username="visitor", password="pw")
        self.assertEqual(self.client.get(url).status_code, 404)                       # signed in, no admin access
        get_user_model().objects.create_superuser("omar", "o@example.com", "pw")
        self.client.login(username="omar", password="pw")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_renditions_are_public_with_a_bounded_cache_lifetime(self):
        image = self.photo_with_gps()
        response = self.client.get(image.get_rendition("width-320|format-webp").url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "public, max-age=3600")

    def test_no_public_page_links_to_an_original_upload(self):
        approve_gallery()
        for path in ("/", "/ar/", "/about/", "/brands/carrier/", "/products/vrf/", "/maintenance/"):
            self.assertNotIn("original_images", self.client.get(path).content.decode(), path)


class FieldPhotoTests(TestCase):
    """The standalone field gallery: what the site shows, the admin area, bulk actions and bulk upload."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def home_html(self, path="/"):
        html = self.client.get(path).content.decode()
        return html.split('id="gallery"')[1].split("</ul>")[0] if 'id="gallery"' in html else ""

    def image(self):
        from core.models import FieldPhoto
        return FieldPhoto.objects.first().image

    def login(self, *codenames, superuser=False):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Permission
        User = get_user_model()
        if superuser:
            User.objects.create_superuser("omar", "o@example.com", "pw")
            self.client.login(username="omar", password="pw")
            return
        user = User.objects.create_user("editor", password="pw")
        user.user_permissions.add(*Permission.objects.filter(codename__in=["access_admin", *codenames]))
        self.client.login(username="editor", password="pw")
        return user

    # ------------------------------------------------------------ public site
    def test_a_fresh_site_shows_no_photo_until_one_is_approved(self):
        from core.models import FieldPhoto
        self.assertEqual(FieldPhoto.objects.count(), 8)
        self.assertEqual(FieldPhoto.objects.filter(approved_for_publication=True).count(), 0)
        html = self.client.get("/").content.decode()
        self.assertNotIn('id="projects"', html)
        self.assertNotIn("data-lightbox", html)

    def test_homepage_shows_only_approved_photos_marked_for_it(self):
        from core.models import FieldPhoto
        photos = field_photos()
        FieldPhoto.objects.filter(pk=photos[0].pk).update(approved_for_publication=True, show_on_homepage=True, home_order=2)
        FieldPhoto.objects.filter(pk=photos[1].pk).update(approved_for_publication=True, show_on_homepage=True, home_order=1)
        FieldPhoto.objects.filter(pk=photos[2].pk).update(approved_for_publication=True)                 # approved, not for home
        FieldPhoto.objects.filter(pk=photos[3].pk).update(show_on_homepage=True, home_order=0)           # for home, not approved
        gallery = self.home_html()
        self.assertEqual(gallery.count("data-lightbox"), 2)
        self.assertLess(gallery.index(photos[1].alt_en), gallery.index(photos[0].alt_en))                # homepage order
        self.assertNotIn(photos[2].alt_en, gallery)
        self.assertNotIn(photos[3].alt_en, gallery)
        self.assertIn(photos[0].title_en, gallery)
        arabic = self.home_html("/ar/")
        self.assertEqual(arabic.count("data-lightbox"), 2)
        self.assertIn(photos[0].title_ar, arabic)

    def test_homepage_never_shows_more_than_eight(self):
        from core.models import FieldPhoto
        FieldPhoto.objects.bulk_create([FieldPhoto(image=self.image(), alt_en=f"Extra {n}", approved_for_publication=True,
                                                   show_on_homepage=True, home_order=50 + n) for n in range(5)])
        approve_gallery()
        self.assertEqual(FieldPhoto.objects.filter(approved_for_publication=True, show_on_homepage=True).count(), 13)
        gallery = self.home_html()
        self.assertEqual(gallery.count("data-lightbox"), 8)
        self.assertNotIn("Extra", gallery)

    def test_withdrawing_approval_removes_the_photo_everywhere_and_keeps_the_record(self):
        from core.models import ContentPage, FieldPhoto, HomePage
        approve_gallery()
        page = ContentPage(title="Gallery", slug="gallery", kind="gallery", title_en="Gallery")
        HomePage.objects.get().add_child(instance=page)
        page.save_revision().publish()
        photo = field_photos()[0]
        self.assertIn(photo.alt_en, self.home_html())
        self.assertIn(photo.alt_en, self.client.get("/gallery/").content.decode())
        FieldPhoto.objects.filter(pk=photo.pk).update(approved_for_publication=False)
        self.assertNotIn(photo.alt_en, self.home_html())
        self.assertNotIn(photo.alt_en, self.client.get("/gallery/").content.decode())
        self.assertEqual(FieldPhoto.objects.count(), 8)

    def test_gallery_is_paginated_and_reads_one_page_at_a_time(self):
        from core.models import ContentPage, FieldPhoto, GalleryCategory, HomePage
        page = ContentPage(title="Gallery", slug="gallery", kind="gallery", title_en="Gallery")
        HomePage.objects.get().add_child(instance=page)
        page.save_revision().publish()
        category = GalleryCategory.objects.create(name_en="Maintenance", name_ar="الصيانة", slug="maintenance")
        image = self.image()
        FieldPhoto.objects.all().delete()
        FieldPhoto.objects.bulk_create([FieldPhoto(image=image, alt_en=f"Photo {n:03d}", sort_order=n, approved_for_publication=True,
                                                   category=category if n < 30 else None) for n in range(60)])
        wall = lambda url: self.client.get(url).content.decode().split('id="gallery"')[1].split("</ul>")[0]
        first = self.client.get("/gallery/")
        self.assertEqual(wall("/gallery/").count("data-lightbox"), 24)
        self.assertEqual(first.context["gallery_page"].paginator.num_pages, 3)
        self.assertIn("Photo 000", wall("/gallery/"))
        self.assertNotIn("Photo 024", wall("/gallery/"))
        html = first.content.decode()
        self.assertIn('rel="next" href="?page=2#photos"', html)
        self.assertNotIn('rel="prev"', html)
        self.assertIn("Page 1 of 3", html)
        self.assertEqual(wall("/gallery/?page=3").count("data-lightbox"), 12)
        self.assertIn("Photo 059", wall("/gallery/?page=3"))
        self.assertEqual(self.client.get("/gallery/?page=99").status_code, 200)       # out of range: last page
        self.assertEqual(self.client.get("/gallery/?page=abc").status_code, 200)      # nonsense: first page
        filtered = self.client.get("/gallery/?category=maintenance")
        self.assertEqual(filtered.context["gallery_page"].paginator.count, 30)
        self.assertIn('href="?category=maintenance&amp;page=2#photos"', filtered.content.decode())
        self.assertIn("الصفحة 1 من 3", self.client.get("/ar/gallery/").content.decode())
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as queries:
            self.client.get("/gallery/?page=2")
        photo_selects = [q["sql"] for q in queries if 'FROM "core_fieldphoto"' in q["sql"] and "COUNT" not in q["sql"]]
        self.assertTrue(any("LIMIT 24" in q for q in photo_selects))
        self.assertFalse([q for q in photo_selects if "LIMIT" not in q and "EXISTS" not in q and "DISTINCT" not in q])

    # ------------------------------------------------------------ the legacy gallery is gone
    def test_legacy_model_table_editor_and_command_are_removed(self):
        import core.models
        from django.core.management import get_commands
        from django.db import connection
        from core.models import HomePage
        self.assertFalse(hasattr(core.models, "GalleryItem"))
        self.assertNotIn("core_galleryitem", connection.introspection.table_names())
        self.assertIn("core_fieldphoto", connection.introspection.table_names())
        self.assertIn("core_gallerycategory", connection.introspection.table_names())
        self.assertNotIn("sync_field_photos", get_commands())
        self.assertFalse(hasattr(HomePage.objects.get(), "gallery"))
        self.login(superuser=True)
        home = HomePage.objects.get()
        html = self.client.get(f"/admin/pages/{home.pk}/edit/").content.decode()
        self.assertNotIn("gallery-0-", html)
        self.assertNotIn("Gallery photos", html)
        self.assertIn("projects_title_en", html)                                     # the section's texts stay editable

    def test_a_home_page_revision_that_still_holds_the_old_rows_publishes_cleanly(self):
        from core.models import FieldPhoto, HomePage
        approve_gallery()
        home = HomePage.objects.get()
        revision = home.save_revision()
        revision.content["gallery"] = [{"pk": 1, "sort_order": 0, "image": FieldPhoto.objects.first().image_id, "page": home.pk,
                                        "alt_en": "Old row", "caption_en": "Old", "approved_for_publication": True}]
        revision.save()
        revision.publish()
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.home_html().count("data-lightbox"), 8)
        self.assertEqual(FieldPhoto.objects.count(), 8)
        self.login(superuser=True)
        self.assertEqual(self.client.get(f"/admin/pages/{home.pk}/edit/").status_code, 200)

    def test_seeded_photos_keep_their_images_texts_and_order(self):
        from core.models import FieldPhoto
        photos = field_photos()
        self.assertEqual([p.image.title for p in photos][:3], ["Gallery: Two inverter condensers beside a villa",
                                                               "Gallery: Crane lifting a package unit onto a roof",
                                                               "Gallery: Rooftop package units on a commercial building"])
        self.assertEqual((photos[0].title_en, photos[0].caption_en), ("Twin Inverter units", "Private villa"))
        self.assertTrue(all(p.title_ar and p.alt_ar for p in photos))
        self.assertEqual(len({p.image_id for p in photos}), 8)
        for p in photos:
            self.assertTrue(p.image.file.storage.exists(p.image.file.name))

    def test_removal_migration_archives_the_rows_and_leaves_everything_else(self):
        """Run 0012 for real: back to 0011, put rows in the old table, forward again."""
        import json
        import tempfile
        from pathlib import Path
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        from django.test import override_settings
        from core.models import FieldPhoto, GalleryCategory
        from wagtail.images.models import Image
        category = GalleryCategory.objects.create(name_en="Maintenance", name_ar="الصيانة", slug="maintenance")
        photos = field_photos()
        FieldPhoto.objects.filter(pk=photos[0].pk).update(legacy_item_id=501, category=category, approved_for_publication=True)
        before = (list(FieldPhoto.objects.order_by("pk").values()), list(GalleryCategory.objects.values()),
                  list(Image.objects.order_by("pk").values_list("pk", "file")))
        files = [p.image.file.name for p in photos]
        executor = MigrationExecutor(connection)
        executor.migrate([("core", "0011_field_photos_switch")])
        old = executor.loader.project_state([("core", "0011_field_photos_switch")]).apps
        Item, Home = old.get_model("core", "GalleryItem"), old.get_model("core", "HomePage")
        home = Home.objects.get()
        Item.objects.create(pk=501, page=home, image_id=photos[0].image_id, sort_order=0, alt_en="Kept alt", alt_ar="نص بديل",
                            caption_en="Kept title", caption_ar="عنوان", subcaption_en="Kept caption", subcaption_ar="تعليق",
                            category_id=category.pk, featured=True, approved_for_publication=True)
        Item.objects.create(pk=502, page=home, image_id=photos[1].image_id, sort_order=1, alt_en="No photo for this one")
        connection.cursor().execute("SET CONSTRAINTS ALL IMMEDIATE")   # the test inserted rows in this same transaction
        with tempfile.TemporaryDirectory() as tmp, override_settings(DATA_DIR=Path(tmp)):
            executor = MigrationExecutor(connection)
            executor.migrate([("core", "0012_remove_legacy_gallery")])
            archives = list((Path(tmp) / "archive").glob("legacy-gallery-items-*.json"))
            self.assertEqual(len(archives), 1)
            rows = json.loads(archives[0].read_text(encoding="utf-8"))["rows"]
        self.assertEqual([r["id"] for r in rows], [501, 502])
        self.assertEqual((rows[0]["caption_ar"], rows[0]["subcaption_ar"], rows[0]["alt_ar"], rows[0]["category_id"],
                          rows[0]["featured"], rows[0]["approved_for_publication"], rows[0]["image_id"]),
                         ("عنوان", "تعليق", "نص بديل", category.pk, True, True, photos[0].image_id))
        self.assertEqual((rows[0]["field_photo_id"], rows[1]["field_photo_id"]), (photos[0].pk, None))
        self.assertNotIn("core_galleryitem", connection.introspection.table_names())
        self.assertEqual((list(FieldPhoto.objects.order_by("pk").values()), list(GalleryCategory.objects.values()),
                          list(Image.objects.order_by("pk").values_list("pk", "file"))), before)
        for name in files:
            self.assertTrue(Image.objects.first().file.storage.exists(name))

    def test_removal_migration_stops_if_the_archive_cannot_be_written(self):
        from pathlib import Path
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        from django.test import override_settings
        photos = field_photos()
        executor = MigrationExecutor(connection)
        executor.migrate([("core", "0011_field_photos_switch")])
        old = executor.loader.project_state([("core", "0011_field_photos_switch")]).apps
        old.get_model("core", "GalleryItem").objects.create(page=old.get_model("core", "HomePage").objects.get(),
                                                            image_id=photos[0].image_id, sort_order=0)
        connection.cursor().execute("SET CONSTRAINTS ALL IMMEDIATE")
        with override_settings(DATA_DIR=Path("/proc/nonexistent/place")):
            with self.assertRaises(OSError):
                MigrationExecutor(connection).migrate([("core", "0012_remove_legacy_gallery")])

    # ------------------------------------------------------------ admin area
    def test_listing_filters_searches_and_paginates(self):
        from core.models import FieldPhoto, GalleryCategory
        self.login(superuser=True)
        dashboard = self.client.get("/admin/").content.decode()
        self.assertIn("Field gallery", dashboard)
        self.assertIn("Upload photos", dashboard)
        self.assertIn("/admin/field-gallery/upload/", dashboard)
        category = GalleryCategory.objects.create(name_en="Maintenance", slug="maintenance")
        FieldPhoto.objects.bulk_create([FieldPhoto(image=self.image(), title_en=f"Bulk {n}", category=category if n % 2 else None)
                                        for n in range(60)])
        url = "/admin/snippets/core/fieldphoto/"
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertIn("<img", page.content.decode())
        self.assertEqual(page.context["page_obj"].paginator.per_page, 50)
        self.assertEqual(page.context["page_obj"].paginator.count, 68)
        self.assertEqual(len(page.context["page_obj"].object_list), 50)
        self.assertEqual(self.client.get(url + "?p=2").status_code, 200)
        self.assertEqual(self.client.get(url, {"category": category.pk}).context["page_obj"].paginator.count, 30)
        self.assertEqual(self.client.get(url, {"approved_for_publication": "true"}).context["page_obj"].paginator.count, 0)
        self.assertEqual(self.client.get(url, {"q": "Bulk 59"}).context["page_obj"].paginator.count, 1)
        html = page.content.decode()
        for label in ("Approve", "Withdraw approval", "Show on home", "Remove from home", "Set category"):
            self.assertIn(label, html)

    def test_each_photo_is_edited_on_its_own_and_only_approvers_can_approve(self):
        from django.contrib.auth.models import Permission
        from core.models import FieldPhoto
        editor = self.login("add_fieldphoto", "change_fieldphoto", "view_fieldphoto")
        photo = FieldPhoto.objects.first()
        url = f"/admin/snippets/core/fieldphoto/edit/{photo.pk}/"
        html = self.client.get(url).content.decode()
        for name in ("alt_en", "alt_ar", "title_en", "title_ar", "caption_en", "caption_ar", "category", "featured",
                     "show_on_homepage", "home_order", "sort_order"):
            self.assertIn(f'name="{name}"', html)
        self.assertNotIn('name="approved_for_publication"', html)
        data = {"image": photo.image_id, "title_en": "Edited by an editor", "home_order": 0, "approved_for_publication": "on"}
        self.assertEqual(self.client.post(url, data).status_code, 302)
        photo.refresh_from_db()
        self.assertEqual(photo.title_en, "Edited by an editor")
        self.assertFalse(photo.approved_for_publication)                             # a forged tick is ignored
        editor.user_permissions.add(Permission.objects.get(codename="approve_fieldphoto"))
        self.client.logout(); self.client.login(username="editor", password="pw")
        self.assertEqual(self.client.post(url, data).status_code, 302)
        photo.refresh_from_db()
        self.assertTrue(photo.approved_for_publication)

    # ------------------------------------------------------------ bulk actions
    def bulk(self, action, ids, data=None):
        url = f"/admin/bulk/core/fieldphoto/{action}/?" + "&".join(f"id={i}" for i in ids)
        return url, self.client.post(url, data or {})

    def test_bulk_approve_and_withdraw(self):
        from core.models import FieldPhoto
        self.login(superuser=True)
        ids = [p.pk for p in field_photos()[:5]]
        confirm = self.client.get(f"/admin/bulk/core/fieldphoto/approve/?" + "&".join(f"id={i}" for i in ids))
        self.assertEqual(confirm.status_code, 200)
        self.assertIn("identifiable face", confirm.content.decode())                 # the reminder before approving
        self.assertEqual(FieldPhoto.objects.filter(approved_for_publication=True).count(), 0)   # opening the page changes nothing
        _, response = self.bulk("approve", ids)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(set(FieldPhoto.objects.filter(approved_for_publication=True).values_list("pk", flat=True)), set(ids))
        _, response = self.bulk("withdraw", ids[:2])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FieldPhoto.objects.filter(approved_for_publication=True).count(), 3)
        self.assertEqual(FieldPhoto.objects.count(), 8)

    def test_bulk_approval_needs_the_approval_permission(self):
        from core.models import FieldPhoto
        self.login("add_fieldphoto", "change_fieldphoto", "view_fieldphoto")
        ids = [p.pk for p in field_photos()[:3]]
        self.bulk("approve", ids)
        self.assertEqual(FieldPhoto.objects.filter(approved_for_publication=True).count(), 0)
        FieldPhoto.objects.update(approved_for_publication=True)
        self.bulk("withdraw", ids)
        self.assertEqual(FieldPhoto.objects.filter(approved_for_publication=True).count(), 8)
        _, response = self.bulk("home_on", ids)                                      # ordinary edits are allowed
        self.assertEqual(FieldPhoto.objects.filter(show_on_homepage=True).count(), 3)

    def test_bulk_actions_are_closed_to_users_without_edit_permission(self):
        from core.models import FieldPhoto
        self.login("view_fieldphoto")
        ids = [p.pk for p in field_photos()[:3]]
        for action in ("approve", "home_on", "set_category"):
            self.bulk(action, ids)
        self.assertEqual(FieldPhoto.objects.filter(approved_for_publication=True).count(), 0)
        self.assertEqual(FieldPhoto.objects.filter(show_on_homepage=True).count(), 0)
        self.client.logout()
        _, response = self.bulk("approve", ids)
        self.assertEqual(response.status_code, 302)                                  # sent to the login page
        self.assertEqual(FieldPhoto.objects.filter(approved_for_publication=True).count(), 0)

    def test_bulk_homepage_and_category(self):
        from core.models import FieldPhoto, GalleryCategory
        self.login(superuser=True)
        category = GalleryCategory.objects.create(name_en="Field Operations", slug="field-operations")
        ids = [p.pk for p in field_photos()[:4]]
        self.bulk("home_on", ids)
        self.assertEqual(FieldPhoto.objects.filter(show_on_homepage=True).count(), 4)
        self.bulk("home_off", ids[:1])
        self.assertEqual(FieldPhoto.objects.filter(show_on_homepage=True).count(), 3)
        self.bulk("set_category", ids, {"category": category.pk})
        self.assertEqual(FieldPhoto.objects.filter(category=category).count(), 4)
        self.bulk("set_category", ids[:2], {"category": ""})
        self.assertEqual(FieldPhoto.objects.filter(category=category).count(), 2)
        self.assertEqual(FieldPhoto.objects.filter(approved_for_publication=True).count(), 0)   # none of this approves anything

    # ------------------------------------------------------------ bulk upload
    def jpeg(self, name, size=(800, 600)):
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image as PILImage
        data = io.BytesIO()
        PILImage.new("RGB", size, (40, 90, 140)).save(data, "JPEG")
        return SimpleUploadedFile(name, data.getvalue(), content_type="image/jpeg")

    def cleanup_images(self, before):
        from wagtail.images.models import Image
        for image in Image.objects.exclude(pk__in=before):
            for rendition in image.renditions.all():
                rendition.file.delete(False)
            image.file.delete(False)

    def test_bulk_upload_uses_wagtails_uploader_and_creates_unapproved_photos(self):
        from core.models import FIELD_GALLERY_COLLECTION, FieldPhoto
        from wagtail.images.models import Image
        from wagtail.models import Collection
        before = set(Image.objects.values_list("pk", flat=True))
        self.addCleanup(self.cleanup_images, before)
        self.login(superuser=True)
        self.assertFalse(Collection.objects.filter(name=FIELD_GALLERY_COLLECTION).exists())     # no migration creates it
        go = self.client.get("/admin/field-gallery/upload/")
        collection = Collection.objects.get(name=FIELD_GALLERY_COLLECTION)
        self.assertRedirects(go, f"/admin/images/multiple/add/?collection_id={collection.pk}", fetch_redirect_response=False)
        page = self.client.get(go.url)
        self.assertEqual(page.status_code, 200)
        self.assertIn("multiple", page.content.decode())                             # Wagtail's multi-file input
        self.assertRegex(page.content.decode(), rf'<option value="{collection.pk}"\s*selected')
        for n in range(3):                                                           # the uploader posts one file per request
            response = self.client.post("/admin/images/multiple/add/", {"files[]": self.jpeg(f"site-{n}.jpg"),
                                                                        "collection": collection.pk},
                                        HTTP_X_REQUESTED_WITH="XMLHttpRequest")
            self.assertTrue(response.json()["success"], response.json())
        new = FieldPhoto.objects.filter(image__collection=collection)
        self.assertEqual(new.count(), 3)
        self.assertEqual(Image.objects.count(), len(before) + 3)                     # one image per file, no copies
        for photo in new:
            self.assertFalse(photo.approved_for_publication)
            self.assertFalse(photo.show_on_homepage)
            self.assertFalse(photo.featured)
            self.assertEqual(photo.image.collection_id, collection.pk)
        self.assertEqual(self.client.get("/admin/field-gallery/upload/").url, go.url)   # the collection is created once
        self.assertEqual(Collection.objects.filter(name=FIELD_GALLERY_COLLECTION).count(), 1)
        self.assertEqual(self.home_html(), "")                                       # nothing is published by uploading
        # Saving an image again never gives it a second photo.
        image = new.first().image
        image.title = "Renamed"
        image.save()
        self.assertEqual(FieldPhoto.objects.filter(image=image).count(), 1)
        # Newest first among photos without a manual order.
        self.assertEqual([p.image.title for p in FieldPhoto.objects.filter(sort_order=None)][-1], "site-0.jpg")

    def test_images_uploaded_elsewhere_do_not_become_field_photos(self):
        from core.models import FieldPhoto, field_gallery_collection
        from wagtail.images.models import Image
        before = set(Image.objects.values_list("pk", flat=True))
        self.addCleanup(self.cleanup_images, before)
        self.login(superuser=True)
        field_gallery_collection(create=True)
        from wagtail.models import Collection
        root = Collection.get_first_root_node()
        response = self.client.post("/admin/images/multiple/add/", {"files[]": self.jpeg("brand-logo.jpg"), "collection": root.pk},
                                    HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertTrue(response.json()["success"])
        self.assertEqual(FieldPhoto.objects.count(), 8)

    def test_upload_validation_is_wagtails(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        from core.models import FieldPhoto, field_gallery_collection
        from wagtail.images.models import Image
        before = set(Image.objects.values_list("pk", flat=True))
        self.addCleanup(self.cleanup_images, before)
        self.login(superuser=True)
        collection = field_gallery_collection(create=True)
        post = lambda f: self.client.post("/admin/images/multiple/add/", {"files[]": f, "collection": collection.pk},
                                          HTTP_X_REQUESTED_WITH="XMLHttpRequest").json()
        not_an_image = post(SimpleUploadedFile("notes.jpg", b"this is not a picture", content_type="image/jpeg"))
        self.assertFalse(not_an_image["success"])
        wrong_type = post(SimpleUploadedFile("script.exe", b"MZ", content_type="application/octet-stream"))
        self.assertFalse(wrong_type["success"])
        with override_settings(WAGTAILIMAGES_MAX_UPLOAD_SIZE=1024):
            too_big = post(self.jpeg("huge.jpg", (1600, 1200)))
        self.assertFalse(too_big["success"])
        self.assertIn("too big", too_big["error_message"].lower())
        self.assertEqual(FieldPhoto.objects.count(), 8)
        self.assertEqual(Image.objects.count(), len(before))

    def test_upload_is_closed_without_permission(self):
        from core.models import FIELD_GALLERY_COLLECTION
        from wagtail.models import Collection
        self.assertEqual(self.client.get("/admin/field-gallery/upload/").status_code, 302)      # not signed in: login
        self.login("view_fieldphoto")
        self.assertIn(self.client.get("/admin/field-gallery/upload/").status_code, (302, 403))
        self.assertFalse(Collection.objects.filter(name=FIELD_GALLERY_COLLECTION).exists())


class MaintenancePageTests(TestCase):
    """Task 17-C: the Maintenance and spare parts page; the duct cleaning page keeps its composition."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def body(self, path):
        html = self.client.get(path).content.decode()
        return html.split('id="app"')[1].split('id="contact"')[0]

    def test_services_are_a_numbered_list_with_the_stored_texts(self):
        from core.models import ServicePage
        page = ServicePage.objects.get(slug="maintenance")
        items = list(page.items.all())
        body = self.body("/maintenance/")
        self.assertEqual(body.count('<li class="svc-item"'), len(items))
        self.assertIn('<ul class="svc-list">', body)
        self.assertNotIn('class="card"', body)
        positions = []
        for n, item in enumerate(items, 1):
            self.assertIn(f'<span class="svc-item__n" aria-hidden="true">{n:02d}</span>', body)
            self.assertIn(f"<h3>{item.title_en}</h3><p>{item.text_en}</p>", body)      # exactly as stored
            positions.append(body.index(item.title_en))
        self.assertEqual(positions, sorted(positions))
        arabic = self.body("/ar/maintenance/")
        for item in items:
            self.assertIn(f"<h3>{item.title_ar}</h3><p>{item.text_ar}</p>", arabic)
        self.assertEqual(self.client.get("/maintenance/").content.decode().count("<h1"), 1)

    def test_the_list_follows_the_number_of_items(self):
        from core.models import ServiceItem, ServicePage
        page = ServicePage.objects.get(slug="maintenance")
        for n in range(7):
            ServiceItem.objects.create(page=page, sort_order=20 + n, title_en=f"Extra {n}", text_en="Text")
        body = self.body("/maintenance/")
        self.assertEqual(body.count('<li class="svc-item"'), 11)
        self.assertIn(">11</span>", body)
        ServiceItem.objects.filter(page=page).delete()
        self.assertNotIn("svc-list", self.body("/maintenance/"))                         # no items: no empty section

    def test_hero_keeps_the_primary_action_and_adds_whatsapp(self):
        from urllib.parse import quote
        from core.models import CompanySettings, ServicePage
        page, number = ServicePage.objects.get(slug="maintenance"), CompanySettings.load().whatsapp
        hero = self.body("/maintenance/").split('class="page-hero__cta"')[1].split("</div>")[0]
        self.assertIn(f'<a class="btn btn-accent" href="#contact">{page.cta_en}</a>', hero)
        message = "Hello, I would like to ask about maintenance and spare parts."
        self.assertIn(f'href="https://wa.me/{number}?text={quote(message)}"', hero)
        self.assertIn('target="_blank" rel="noopener"', hero)
        arabic = self.body("/ar/maintenance/").split('class="page-hero__cta"')[1].split("</div>")[0]
        self.assertIn(page.cta_ar, arabic)
        self.assertIn(f"https://wa.me/{number}?text={quote('مرحباً، أودّ الاستفسار عن الصيانة وقطع الغيار.')}", arabic)
        self.assertIn("واتساب", arabic)

    def test_other_services_lists_published_service_pages_except_this_one(self):
        from core.models import ServicePage
        duct = ServicePage.objects.get(slug="duct-cleaning")
        if not duct.live:
            duct.save_revision().publish()
        section = self.body("/maintenance/").split('other-services">')[1].split("</section>")[0]
        self.assertIn("<h2>Other HVAC services</h2>", section)
        self.assertEqual(section.count('class="service-row"'), 1)
        self.assertIn('href="/duct-cleaning/"', section)
        self.assertNotIn('href="/maintenance/"', section)
        self.assertIn(duct.title_en, section)
        self.assertEqual(self.client.get("/duct-cleaning/").status_code, 200)
        arabic = self.body("/ar/maintenance/").split('other-services">')[1].split("</section>")[0]
        self.assertIn("خدمات تكييف أخرى", arabic)
        self.assertIn('href="/ar/duct-cleaning/"', arabic)
        duct.unpublish()                                                                 # nothing else published: no section, no dead link
        body = self.body("/maintenance/")
        self.assertNotIn("other-services", body)
        self.assertNotIn("/duct-cleaning/", body)

    def test_no_brand_grid_and_the_quote_form_is_unchanged(self):
        html = self.client.get("/maintenance/").content.decode()
        self.assertNotIn("brand-wall", html.split('id="app"')[1].split('id="contact"')[0])
        form = html.split('id="contact"')[1]
        self.assertRegex(form, r'<option value="maintenance"[^>]*selected')
        self.assertIn('name="phone"', form)


class DuctCleaningPageTests(TestCase):
    """Task 17-D: the AC duct cleaning page; the maintenance page keeps its approved composition."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)
        from core.models import ServicePage
        page = ServicePage.objects.get(slug="duct-cleaning")
        if not page.live:
            page.save_revision().publish()

    def page(self):
        from core.models import ServicePage
        return ServicePage.objects.get(slug="duct-cleaning")

    def body(self, path):
        return self.client.get(path).content.decode().split('id="app"')[1].split('id="contact"')[0]

    def wa_text(self, path):
        import re
        from urllib.parse import unquote
        from core.models import CompanySettings
        hero = self.body(path).split('class="page-hero__cta"')[1].split("</div>")[0]
        number = CompanySettings.load().whatsapp
        encoded = re.search(rf'href="https://wa\.me/{number}\?text=([^"]*)"', hero).group(1)
        self.assertNotRegex(encoded, r"[\s<>]")                                      # fully URL-encoded
        return unquote(encoded)

    def test_items_are_a_definition_list_with_the_stored_texts(self):
        items = list(self.page().items.all())
        self.assertEqual(len(items), 4)
        body = self.body("/duct-cleaning/")
        self.assertEqual(body.count('<dl class="prep__list">'), 1)
        self.assertEqual(body.count("<dt>"), 4)
        self.assertEqual(body.count("<dd>"), 4)
        self.assertIn(f'<h2 class="prep__title">{self.page().list_title_en}</h2>', body)
        positions = []
        for item in items:
            self.assertIn(f'<dt><span class="prep__dot" aria-hidden="true"></span>{item.title_en}</dt><dd>{item.text_en}</dd>', body)
            positions.append(body.index(item.title_en + "</dt>"))
        self.assertEqual(positions, sorted(positions))
        arabic = self.body("/ar/duct-cleaning/")
        for item in items:
            self.assertIn(f"{item.title_ar}</dt><dd>{item.text_ar}</dd>", arabic)
        for needle in ('class="card"', "svc-list", "cta-band", "✓"):                   # no cards, no numbered list, no second action bar, no ticks
            self.assertNotIn(needle, body)
        self.assertEqual(self.client.get("/duct-cleaning/").content.decode().count("<h1"), 1)

    def test_the_sheet_follows_the_number_of_items(self):
        from core.models import ServiceItem
        page = self.page()
        ServiceItem.objects.create(page=page, sort_order=30, title_en="Extra detail", title_ar="تفصيل إضافي", text_en="Text")
        self.assertEqual(self.body("/duct-cleaning/").count("<dt>"), 5)
        ServiceItem.objects.filter(page=page).delete()
        body = self.body("/duct-cleaning/")
        self.assertNotIn("prep", body)                                               # empty list: no empty sheet
        self.assertEqual(self.client.get("/duct-cleaning/").status_code, 200)

    def test_whatsapp_message_lists_the_item_headings_in_the_page_language(self):
        items = list(self.page().items.all())
        self.assertEqual(self.wa_text("/duct-cleaning/"),
                         "Hello, I would like to ask about AC duct cleaning.\n\n" + "\n".join(f"{i.title_en}:" for i in items))
        arabic = self.wa_text("/ar/duct-cleaning/")
        self.assertEqual(arabic, "مرحباً، أودّ الاستفسار عن تنظيف مجاري التكييف.\n\n" + "\n".join(f"{i.title_ar}:" for i in items))
        for item in items:
            self.assertNotIn(item.text_en, self.wa_text("/duct-cleaning/"))           # descriptions stay out of the message
        hero = self.body("/duct-cleaning/").split('class="page-hero__cta"')[1].split("</div>")[0]
        self.assertIn(f'<a class="btn btn-accent" href="#contact">{self.page().cta_en}</a>', hero)
        self.assertIn('target="_blank" rel="noopener"', hero)

    def test_whatsapp_message_copes_with_missing_and_changed_items(self):
        from core.models import ServiceItem
        page = self.page()
        items = list(page.items.all())
        ServiceItem.objects.filter(pk=items[1].pk).update(title_en="   ", title_ar="")           # an empty heading is skipped
        ServiceItem.objects.filter(pk=items[2].pk).update(title_en="Site & floor #2", title_ar="")  # no Arabic: falls back, needs encoding
        text = self.wa_text("/duct-cleaning/")
        self.assertEqual(text.split("\n")[2:], [f"{items[0].title_en}:", "Site & floor #2:", f"{items[3].title_en}:"])
        self.assertIn("Site & floor #2:", self.wa_text("/ar/duct-cleaning/"))
        ServiceItem.objects.filter(page=page).delete()
        self.assertEqual(self.wa_text("/duct-cleaning/"), "Hello, I would like to ask about AC duct cleaning.")
        self.assertEqual(self.wa_text("/ar/duct-cleaning/"), "مرحباً، أودّ الاستفسار عن تنظيف مجاري التكييف.")

    def test_other_services_links_to_maintenance_only_while_it_is_published(self):
        from core.models import ServicePage
        section = self.body("/duct-cleaning/").split('other-services">')[1].split("</section>")[0]
        self.assertEqual(section.count('class="service-row"'), 1)
        self.assertIn('href="/maintenance/"', section)
        self.assertNotIn('href="/duct-cleaning/"', section)
        self.assertIn('href="/ar/maintenance/"', self.body("/ar/duct-cleaning/").split('other-services">')[1])
        ServicePage.objects.get(slug="maintenance").unpublish()
        self.assertNotIn("other-services", self.body("/duct-cleaning/"))

    def test_maintenance_page_and_quote_form_are_unchanged(self):
        from core.models import ServicePage
        maintenance = self.body("/maintenance/")
        self.assertEqual(maintenance.count('<li class="svc-item"'), ServicePage.objects.get(slug="maintenance").items.count())
        self.assertIn('<span class="svc-item__n" aria-hidden="true">01</span>', maintenance)
        self.assertNotIn("prep__", maintenance)
        self.assertIn("maintenance%20and%20spare%20parts", maintenance)
        section = maintenance.split('other-services">')[1].split("</section>")[0]
        self.assertIn('href="/duct-cleaning/"', section)
        form = self.client.get("/duct-cleaning/").content.decode().split('id="contact"')[1]
        self.assertRegex(form, r'<option value="duct-cleaning"[^>]*selected')
        for field in ('name="name"', 'name="phone"', 'name="unit"', 'name="brand"', 'name="emirate"', 'name="notes"'):
            self.assertIn(field, form)

    def test_a_future_service_page_keeps_the_plain_composition(self):
        from core.models import HomePage, ServiceItem, ServicePage
        page = ServicePage(title="Other", slug="other-service", title_en="Other service", form_value="other")
        HomePage.objects.get().add_child(instance=page)
        ServiceItem.objects.create(page=page, sort_order=0, title_en="One", text_en="Text")
        page.save_revision().publish()
        body = self.body("/other-service/")
        self.assertIn('<div class="card" data-reveal>', body)
        self.assertNotIn("prep__", body)
        self.assertNotIn("svc-list", body)


class AboutPageTests(TestCase):
    """Task 17-E: the About page; the other content pages keep their composition."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def page(self):
        from core.models import ContentPage
        return ContentPage.objects.get(slug="about")

    def body(self, path):
        return self.client.get(path).content.decode().split('id="app"')[1].split("</main>")[0].split('id="contact"')[0]

    def test_title_lead_and_sections_are_shown_exactly_and_in_order(self):
        import html
        page = self.page()
        sections = list(page.sections.all())
        self.assertGreaterEqual(len(sections), 2)
        for path, lang in (("/about/", "en"), ("/ar/about/", "ar")):
            body = html.unescape(self.body(path))
            self.assertIn(f"<h1>{getattr(page, f'title_{lang}')}</h1>", body)
            self.assertIn(f'<p class="lead">{getattr(page, f"lead_{lang}")}</p>', body)
            self.assertEqual(body.count('<section class="about-sec">'), len(sections))
            positions = []
            for sec in sections:
                heading = getattr(sec, f"heading_{lang}")
                self.assertIn(f"<h2>{heading}</h2>", body)
                positions.append(body.index(f"<h2>{heading}</h2>"))
                for line in getattr(sec, f"body_{lang}").splitlines():
                    line = line.strip()
                    if line:
                        self.assertIn(line[1:].strip() if line.startswith("-") else line, body)   # every paragraph and list item
            self.assertEqual(positions, sorted(positions))
        self.assertEqual(self.client.get("/about/").content.decode().count("<h1"), 1)

    def test_the_layout_follows_the_number_of_sections(self):
        from core.models import ContentSection
        page = self.page()
        ContentSection.objects.create(page=page, sort_order=50, heading_en="Added later", body_en="One paragraph.\n\n- first\n- second")
        body = self.body("/about/")
        self.assertEqual(body.count('<section class="about-sec">'), page.sections.count())
        self.assertIn("<li>first</li><li>second</li>", body)
        ContentSection.objects.filter(page=page).delete()
        self.assertEqual(self.client.get("/about/").status_code, 200)
        self.assertNotIn("about-sec", self.body("/about/"))

    def test_hero_has_contact_and_whatsapp_actions(self):
        from urllib.parse import quote
        from core.models import CompanySettings, ContentPage, SiteCopy
        number = CompanySettings.load().whatsapp
        hero = self.body("/about/").split('class="page-hero__cta"')[1].split("</div>")[0]
        self.assertIn(f'<a class="btn btn-accent" href="/contact/">{SiteCopy.load().nav_contact_en}</a>', hero)
        self.assertIn(f'href="https://wa.me/{number}?text={quote("Hello, I have an inquiry for Opal Galaxy.")}"', hero)
        self.assertIn('target="_blank" rel="noopener"', hero)
        arabic = self.body("/ar/about/").split('class="page-hero__cta"')[1].split("</div>")[0]
        self.assertIn('href="/ar/contact/"', arabic)
        self.assertIn(quote("مرحباً، لديّ استفسار لشركة Opal Galaxy."), arabic)
        ContentPage.objects.get(slug="contact").unpublish()                             # no contact page: no dead link
        hero = self.body("/about/").split('class="page-hero__cta"')[1].split("</div>")[0]
        self.assertNotIn("/contact/", hero)
        self.assertIn("wa.me", hero)

    def test_company_details_come_from_the_settings_without_hours_or_licence(self):
        from core.models import CompanySettings
        s = CompanySettings.load()
        panel = self.body("/about/").split('class="about__aside"')[1].split("</aside>")[0]
        self.assertEqual(panel.count("<dt>"), 4)
        for value in (s.legal_name, s.address, s.phone_display or s.phone, s.email):
            self.assertIn(value, panel)
        self.assertIn(f'href="tel:{s.phone}"', panel)
        self.assertIn(f'href="mailto:{s.email}"', panel)
        whole = self.body("/about/")
        for held_back in (s.hours_full_en, s.hours_short_en, s.licence_en, "Business hours", "Licence"):
            if held_back:
                self.assertNotIn(held_back, whole)
        arabic = self.body("/ar/about/")
        self.assertIn("بيانات الشركة", arabic)
        self.assertIn("الاسم القانوني", arabic)
        for held_back in (s.hours_full_ar, s.licence_ar):
            if held_back:
                self.assertNotIn(held_back, arabic)
        CompanySettings.objects.update(email="", address="")                           # an empty value drops its row
        panel = self.body("/about/").split('class="about__aside"')[1].split("</aside>")[0]
        self.assertEqual(panel.count("<dt>"), 2)
        self.assertEqual(CompanySettings.load().legal_name, s.legal_name)               # nothing stored was changed by rendering

    def test_explore_links_point_only_to_published_pages(self):
        import re
        from core.models import ContentPage, HomePage, ServicePage
        section = self.body("/about/").split('class="section section--ruled explore"')[1].split("</section>")[0]
        hrefs = re.findall(r'class="explore__link" href="([^"]+)"', section)
        self.assertEqual(hrefs[0], "/#brands")
        self.assertEqual(len(hrefs), len(set(hrefs)))
        for href in hrefs[1:]:
            self.assertEqual(self.client.get(href).status_code, 200, href)
        self.assertIn("/maintenance/", hrefs)
        self.assertNotIn("/gallery/", hrefs)                                            # no gallery page yet
        self.assertNotIn("brand-wall", self.body("/about/"))                            # no grid of manufacturer names
        gallery = ContentPage(title="Gallery", slug="gallery", kind="gallery", title_en="Gallery")
        HomePage.objects.get().add_child(instance=gallery)
        gallery.save_revision().publish()
        ServicePage.objects.get(slug="maintenance").unpublish()
        section = self.body("/about/").split('class="section section--ruled explore"')[1].split("</section>")[0]
        hrefs = re.findall(r'class="explore__link" href="([^"]+)"', section)
        self.assertIn("/gallery/", hrefs)
        self.assertNotIn("/maintenance/", hrefs)
        self.assertIn('href="/ar/#brands"', self.body("/ar/about/"))

    def test_quote_form_follows_the_page_option(self):
        from core.models import ContentPage
        self.assertIn('id="contact"', self.client.get("/about/").content.decode())
        ContentPage.objects.filter(slug="about").update(show_quote_form=False)
        self.assertNotIn('id="contact"', self.client.get("/about/").content.decode())

    def test_other_content_pages_keep_their_composition(self):
        for path in ("/faq/", "/contact/", "/privacy/"):
            html = self.client.get(path).content.decode()
            body = html.split('id="app"')[1].split("</main>")[0]
            for needle in ("about-sec", "about__aside", "explore__link", "page-hero--text"):
                self.assertNotIn(needle, body, path)
            self.assertIn('<section class="page-hero">', body)
        self.assertIn('class="prose__section"', self.client.get("/privacy/").content.decode())
        self.assertIn('class="faq-list"', self.client.get("/faq/").content.decode())
        self.assertIn('class="contact-cards"', self.client.get("/contact/").content.decode())


class ContactPageTests(TestCase):
    """Task 17-F: the Contact page; About, FAQ, Privacy and the shared form are unchanged."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def section(self, path="/contact/"):
        html = self.client.get(path).content.decode()
        return html.split('aria-labelledby="contact-methods"')[1].split("</section>")[0]

    def settings(self):
        from core.models import CompanySettings
        return CompanySettings.load()

    def test_three_cards_in_order_with_the_values_from_company_details(self):
        import re
        s = self.settings()
        section = self.section()
        hrefs = re.findall(r'<a class="contact-card[^"]*" href="([^"]+)"', section)
        self.assertEqual(hrefs, [f"https://wa.me/{s.whatsapp}", f"tel:{s.phone}", f"mailto:{s.email}"])
        labels = re.findall(r'class="contact-card__label">([^<]+)<', section)
        self.assertEqual(labels, ["WhatsApp", "Telephone", "Email"])
        values = re.findall(r'class="contact-card__value ltr">([^<]+)<', section)
        self.assertEqual(values, [s.phone_display, s.phone_display, s.email])
        self.assertIn('target="_blank" rel="noopener"', section.split("contact-card--wa")[1].split(">")[0])
        self.assertEqual(section.count("<a "), 3)                                   # one link per card, nothing else
        self.assertEqual(section.count("<svg"), 6)                                  # an icon and an arrow each, decorative
        self.assertEqual(section.count('class="contact-card__icon" aria-hidden="true"'), 3)
        self.assertEqual(section.count('class="contact-card__go icon-dir" aria-hidden="true"'), 3)
        self.assertIn('<h2 class="visually-hidden" id="contact-methods">Contact methods</h2>', section)
        arabic = self.section("/ar/contact/")
        self.assertEqual(re.findall(r'class="contact-card__label">([^<]+)<', arabic), ["واتساب", "الهاتف", "البريد الإلكتروني"])
        self.assertEqual(re.findall(r'class="contact-card__value ltr">([^<]+)<', arabic), values)   # numbers and addresses stay left-to-right

    def test_each_value_appears_once_in_the_section(self):
        s = self.settings()
        section = self.section()
        self.assertEqual(section.count(s.email), 2)                                 # the link address and the visible text
        self.assertEqual(section.count(f"tel:{s.phone}"), 1)
        self.assertEqual(section.count(f"wa.me/{s.whatsapp}"), 1)
        for old in ('class="kv"', "contact-actions", "btn-outline"):
            self.assertNotIn(old, section)

    def test_office_information_shows_the_address_only(self):
        s = self.settings()
        section = self.section()
        office = section.split('class="office"')[1]
        self.assertIn("<h2 class=\"office__title\">Office information</h2>", office)
        self.assertEqual(office.count("<dt>"), 1)
        self.assertIn(f'<dt>Address</dt><dd><span class="ltr">{s.address}</span></dd>', office)
        self.assertTrue(s.hours_full_en and s.licence_en)                           # still stored, just not shown here
        for held_back in (s.hours_full_en, s.hours_short_en, s.licence_en, "Business hours", "Licence"):
            self.assertNotIn(held_back, section)
        arabic = self.section("/ar/contact/")
        self.assertIn("بيانات المكتب", arabic)
        for held_back in (s.hours_full_ar, s.licence_ar, "ساعات العمل"):
            self.assertNotIn(held_back, arabic)

    def test_empty_values_drop_their_card_or_row(self):
        from core.models import CompanySettings
        before = self.settings()
        CompanySettings.objects.update(email="", address="")
        section = self.section()
        self.assertEqual(section.count('<a class="contact-card'), 2)
        self.assertNotIn("mailto:", section)
        self.assertNotIn('class="office"', section)
        self.assertEqual(self.client.get("/contact/").status_code, 200)
        CompanySettings.objects.update(whatsapp="971500000000")                      # a different WhatsApp number is shown as it is
        self.assertIn('class="contact-card__value ltr">+971500000000<', self.section())
        after = self.settings()
        self.assertEqual((after.hours_full_en, after.licence_en, after.phone), (before.hours_full_en, before.licence_en, before.phone))

    def test_hero_has_no_buttons_and_keeps_the_stored_title_and_lead(self):
        from core.models import ContentPage
        page = ContentPage.objects.get(slug="contact")
        html = self.client.get("/contact/").content.decode()
        hero = html.split('<section class="page-hero">')[1].split("</section>")[0]
        self.assertIn(f"<h1>{page.title_en}</h1>", hero)
        self.assertIn(page.lead_en, hero)
        self.assertNotIn("<a ", hero)
        self.assertEqual(html.count("<h1"), 1)

    def test_page_sections_from_the_admin_still_render(self):
        from core.models import ContentPage, ContentSection
        page = ContentPage.objects.get(slug="contact")
        ContentSection.objects.create(page=page, sort_order=0, heading_en="Before you call", body_en="Have the model number ready.")
        html = self.client.get("/contact/").content.decode()
        self.assertIn("<h2>Before you call</h2>", html)
        self.assertLess(html.index("Before you call"), html.index("contact-cards"))

    def test_shared_form_header_and_footer_are_unchanged(self):
        s = self.settings()
        html = self.client.get("/contact/").content.decode()
        form = html.split('id="contact"')[1].split("</section>")[0]
        for field in ('name="name"', 'name="phone"', 'name="unit"', 'name="brand"', 'name="qty"', 'name="emirate"', 'name="notes"'):
            self.assertIn(field, form)
        self.assertIn('action="/quote/"', form)
        header = html.split("<header")[1].split("</header>")[0]
        self.assertIn(f'href="tel:{s.phone}"', header)
        self.assertIn(f"https://wa.me/{s.whatsapp}", header)
        footer = html.split("<footer")[1]
        self.assertIn(f'href="tel:{s.phone}"', footer)
        self.assertIn(f'href="mailto:{s.email}"', footer)

    def test_other_content_pages_do_not_get_the_contact_components(self):
        for path in ("/about/", "/faq/", "/privacy/"):
            body = self.client.get(path).content.decode().split('id="app"')[1].split("</main>")[0]
            for needle in ("contact-card", 'class="office"'):
                self.assertNotIn(needle, body, path)
        self.assertIn('class="about__aside"', self.client.get("/about/").content.decode())


class FaqPageTests(TestCase):
    """Task 17-G: the FAQ page shows every answer; the home page keeps its accordion."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def body(self, path="/faq/"):
        return self.client.get(path).content.decode().split('id="app"')[1].split('id="contact"')[0]

    def items(self):
        from core.models import FaqItem
        return list(FaqItem.objects.all())

    def test_every_question_is_a_heading_with_its_answer_visible_in_order(self):
        import html
        from core.models import FaqItem
        FaqItem.objects.filter(pk=self.items()[1].pk).update(featured=False)       # not on the home page, still here
        items = self.items()
        self.assertEqual(len(items), 6)
        for path, lang in (("/faq/", "en"), ("/ar/faq/", "ar")):
            body = html.unescape(self.body(path))
            self.assertEqual(body.count('<article class="faq-item">'), 6)
            positions = []
            for item in items:
                question, answer = getattr(item, f"question_{lang}"), getattr(item, f"answer_{lang}")
                self.assertIn(f"<h2>{question}</h2>", body)
                self.assertIn(f"<p>{answer}</p>", body)
                positions.append(body.index(f"<h2>{question}</h2>"))
            self.assertEqual(positions, sorted(positions))
            for needle in ("<details", "<summary", "accordion", "application/ld+json"):   # nothing hidden, no schema added
                self.assertNotIn(needle, body)
        self.assertEqual(self.client.get("/faq/").content.decode().count("<h1"), 1)

    def test_answers_keep_their_paragraphs_and_line_breaks_and_are_escaped(self):
        from core.models import FaqItem
        first, second, third = self.items()[:3]
        FaqItem.objects.filter(pk=first.pk).update(answer_en="First paragraph.\n\n\n\nSecond paragraph,\nsecond line.\r\n\r\nThird.")
        FaqItem.objects.filter(pk=second.pk).update(answer_en="<script>alert(1)</script> & <b>bold</b>")
        FaqItem.objects.filter(pk=third.pk).update(answer_en="   ", answer_ar="")
        body = self.body()
        self.assertIn("<p>First paragraph.</p><p>Second paragraph,<br>second line.</p><p>Third.</p>", body)
        self.assertNotIn("<p></p>", body)
        self.assertNotIn("<script>alert(1)</script>", body)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt; &amp; &lt;b&gt;bold&lt;/b&gt;", body)
        blank = body.split(f"<h2>{third.question_en}</h2>")[1].split("</article>")[0]
        self.assertNotIn("<p>", blank)                                             # a blank answer leaves the heading alone
        self.assertEqual(FaqItem.objects.get(pk=first.pk).answer_en,
                         "First paragraph.\n\n\n\nSecond paragraph,\nsecond line.\r\n\r\nThird.")   # stored text untouched by rendering

    def test_any_number_of_questions_including_none(self):
        from core.models import FaqItem, HomePage
        home = HomePage.objects.get()
        for n in range(20):
            FaqItem.objects.create(page=home, sort_order=50 + n, question_en=f"Extra question {n}?", answer_en="Answer.")
        self.assertEqual(self.body().count('<article class="faq-item">'), 26)
        FaqItem.objects.all().delete()
        response = self.client.get("/faq/")
        self.assertEqual(response.status_code, 200)
        body = self.body()
        self.assertNotIn("faq-list", body)
        self.assertIn("faq-next", body)

    def test_contact_actions_follow_the_list_once(self):
        from urllib.parse import quote
        from core.models import CompanySettings, ContentPage, SiteCopy
        number = CompanySettings.load().whatsapp
        body = self.body()
        self.assertEqual(body.count("faq-next__actions"), 1)
        self.assertLess(body.index("faq-list"), body.index("faq-next__actions"))
        actions = body.split('class="faq-next__actions"')[1].split("</div>")[0]
        self.assertIn(f'<a class="btn btn-primary" href="/contact/">{SiteCopy.load().nav_contact_en}</a>', actions)
        self.assertIn(f'href="https://wa.me/{number}?text={quote("Hello, I have an inquiry for Opal Galaxy.")}"', actions)
        self.assertEqual(body.count("wa.me"), 1)                                    # not repeated after every question
        arabic = self.body("/ar/faq/").split('class="faq-next__actions"')[1].split("</div>")[0]
        self.assertIn('href="/ar/contact/"', arabic)
        self.assertIn("واتساب", arabic)
        self.assertEqual(self.client.get("/contact/").status_code, 200)
        ContentPage.objects.get(slug="contact").unpublish()
        actions = self.body().split('class="faq-next__actions"')[1].split("</div>")[0]
        self.assertNotIn("/contact/", actions)
        self.assertIn("wa.me", actions)

    def test_home_page_accordion_and_its_selection_are_unchanged(self):
        from core.models import FaqItem
        FaqItem.objects.filter(pk=self.items()[0].pk).update(featured=False)
        home = self.client.get("/").content.decode().split('id="faq"')[1].split("</section>")[0]
        self.assertIn('<div class="accordion">', home)
        self.assertEqual(home.count("<details>"), 5)
        self.assertNotIn(self.items()[0].question_en, home)
        self.assertIn(self.items()[0].question_en, self.body())
        self.assertNotIn("faq-item", home)

    def test_other_pages_and_the_form_are_unchanged(self):
        for path, marker in (("/about/", 'class="about__aside"'), ("/contact/", 'class="contact-cards"'),
                             ("/privacy/", 'class="prose__section"'), ("/maintenance/", 'class="svc-list"'),
                             ("/duct-cleaning/", 'class="prep__list"')):
            html = self.client.get(path).content.decode()
            self.assertIn(marker, html, path)
            for needle in ("faq-item", "faq-next"):
                self.assertNotIn(needle, html, path)
        form = self.client.get("/faq/").content.decode().split('id="contact"')[1]
        for field in ('name="name"', 'name="phone"', 'name="unit"', 'name="notes"'):
            self.assertIn(field, form)


class PrivacyPageTests(TestCase):
    """Task 17-H: the Privacy Policy keeps its stored text and gets a plain document style with a print style."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def page(self):
        from core.models import ContentPage
        return ContentPage.objects.get(slug="privacy")

    def body(self, path="/privacy/"):
        return self.client.get(path).content.decode().split('id="app"')[1].split('id="contact"')[0]

    def test_stored_text_is_shown_exactly_and_in_order(self):
        import html
        page = self.page()
        sections = list(page.sections.all())
        self.assertEqual(len(sections), 8)
        for path, lang in (("/privacy/", "en"), ("/ar/privacy/", "ar")):
            body = html.unescape(self.body(path))
            self.assertIn(f"<h1>{getattr(page, f'title_{lang}')}</h1>", body)
            self.assertIn(getattr(page, f"lead_{lang}"), body)
            self.assertEqual(body.count('class="prose__section"'), 8)
            visible = __import__("re").sub(r"<[^>]+>", "", body)
            positions = []
            for sec in sections:
                heading = getattr(sec, f"heading_{lang}")
                self.assertIn(f"<h2>{heading}</h2>", body)
                positions.append(body.index(f"<h2>{heading}</h2>"))
                for line in getattr(sec, f"body_{lang}").splitlines():
                    line = line.strip()
                    if line:
                        self.assertIn(line[1:].strip() if line.startswith("-") else line, visible)
            self.assertEqual(positions, sorted(positions))
        self.assertEqual(self.client.get("/privacy/").content.decode().count("<h1"), 1)

    def test_lists_paragraphs_and_the_mail_link_render_as_markup(self):
        body = self.body()
        self.assertIn('<div class="prose prose--doc">', body)
        self.assertEqual(body.count("<li>"), 8)
        self.assertIn("<ul><li>Name (optional)</li>", body)
        self.assertIn('<a href="mailto:info@opalgalaxy.ae">info@opalgalaxy.ae</a>', body)
        self.assertNotIn("<p></p>", body)

    def test_text_typed_in_the_admin_is_escaped(self):
        from core.models import ContentSection
        sec = self.page().sections.first()
        ContentSection.objects.filter(pk=sec.pk).update(body_en="<script>alert(1)</script>\n\n- <b>item</b>")
        body = self.body()
        self.assertNotIn("<script>alert(1)</script>", body)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", body)
        self.assertIn("<li>&lt;b&gt;item&lt;/b&gt;</li>", body)

    def test_nothing_is_added_to_the_policy(self):
        import re
        visible = re.sub(r"<[^>]+>", " ", self.body())
        for added in ("Last updated", "Analytics", "retention", "Table of contents"):
            self.assertNotIn(added, visible)
        self.assertNotRegex(visible, r"20\d\d")                                     # no date invented
        for needle in ("btn-wa", "faq-next", "explore__link", "contact-card", "<details"):   # no calls to action or widgets
            self.assertNotIn(needle, self.body())

    def test_print_style_is_scoped_to_the_policy(self):
        from django.conf import settings
        css = (settings.BASE_DIR / "static/css/components.css").read_text()
        block = css.split("@media print{")[1].split("\n}")[0]
        for line in block.strip().splitlines():
            self.assertIn(".prose--doc", line)                                      # every print rule needs the policy on the page
        for hidden in (".site-header", ".mbar", "#contact", ".site-footer"):
            self.assertIn(f"body:has(.prose--doc) {hidden}", block)

    def test_other_pages_do_not_get_the_document_style(self):
        for path, marker in (("/about/", 'class="about__aside"'), ("/faq/", 'class="faq-list"'), ("/contact/", 'class="contact-cards"'),
                             ("/maintenance/", 'class="svc-list"'), ("/duct-cleaning/", 'class="prep__list"')):
            html = self.client.get(path).content.decode()
            self.assertIn(marker, html, path)
            self.assertNotIn("prose--doc", html, path)
        form = self.client.get("/privacy/").content.decode().split('id="contact"')[1]
        for field in ('name="phone"', 'name="unit"', 'name="notes"'):
            self.assertIn(field, form)

    def test_a_future_text_page_keeps_the_plain_prose(self):
        from core.models import ContentPage, ContentSection, HomePage
        page = ContentPage(title="Terms", slug="terms", kind="text", title_en="Terms")
        HomePage.objects.get().add_child(instance=page)
        ContentSection.objects.create(page=page, sort_order=0, heading_en="One", body_en="Text")
        page.save_revision().publish()
        html = self.client.get("/terms/").content.decode()
        self.assertIn('<div class="prose">', html)
        self.assertNotIn("prose--doc", html)


class BreadcrumbTests(TestCase):
    """The breadcrumb's links, separators and current page sit on one centre line."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def test_every_item_is_centred_on_the_same_line(self):
        from django.conf import settings
        css = (settings.BASE_DIR / "static/css/components.css").read_text()
        self.assertIn(".crumbs{align-items:center}", css)
        self.assertRegex(css, r"\.crumbs span\{display:inline-flex;align-items:center;min-block-size:2rem\}")
        self.assertIn(".crumbs a{display:inline-flex;align-items:center;min-block-size:2rem}", css)   # the link keeps its touch height
        # Arabic: the separator rule must not put a "/" before the first item.
        self.assertLess(css.index('[dir=rtl] .crumbs span::before{content:"/"}'),
                        css.index("[dir=rtl] .crumbs span:first-child::before{content:none}"))

    def test_markup_is_unchanged_on_every_page_type(self):
        for path, trail in (("/privacy/", ["Home", "Privacy Policy"]), ("/about/", ["Home", "About Opal Galaxy"]),
                            ("/maintenance/", ["Home", "Maintenance and spare parts"]),
                            ("/brands/carrier/", ["Home", "Brands", "Carrier"]), ("/products/vrf/", ["Home", "Products", "VRF systems"])):
            import re
            html = self.client.get(path).content.decode()
            nav = html.split('<nav class="crumbs wrap"')[1].split("</nav>")[0]
            self.assertEqual([re.sub(r"<[^>]+>", "", x) for x in re.findall(r"<span>(.*?)</span>", nav)], trail, path)
            self.assertEqual(nav.count("<a "), len(trail) - 1)            # the current page is text, not a link
        self.assertIn('aria-label="مسار التنقل"', self.client.get("/ar/about/").content.decode())


class HeadingOrderTests(TestCase):
    """QA-03: no heading level is skipped on the internal pages (h2 is followed by h3, not h4)."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def levels(self, path):
        import re
        html = self.client.get(path).content.decode()
        body = html.split('id="app"')[1].split("</main>")[0]
        return [int(n) for n in re.findall(r"<h([1-6])[\s>]", body)]

    def test_technical_panels_use_h3_under_the_section_h2(self):
        from catalog.models import Brand, ProductCategory
        paths = [b.get_url() for b in Brand.objects.all()] + [c.get_url() for c in ProductCategory.objects.live()]
        self.assertGreaterEqual(len(paths), 20)
        with_panels = 0
        for base in paths:
            for path in (base, "/ar" + base):
                html = self.client.get(path).content.decode()
                self.assertNotIn("<h4", html.split('id="app"')[1].split('id="contact"')[0], path)
                if 'class="tech__heading"' in html:
                    with_panels += 1
                    self.assertIn('<h3 class="tech__heading">', html)
                levels = self.levels(path)
                self.assertEqual(levels[0], 1, path)
                for previous, current in zip(levels, levels[1:]):
                    self.assertLessEqual(current - previous, 1, f"{path}: h{previous} followed by h{current}")
        self.assertGreater(with_panels, 0)

    def test_other_internal_pages_skip_no_level_either(self):
        for path in ("/maintenance/", "/duct-cleaning/", "/about/", "/contact/", "/faq/", "/privacy/",
                     "/ar/maintenance/", "/ar/about/", "/ar/faq/"):
            levels = self.levels(path)
            self.assertEqual(levels.count(1), 1, path)
            for previous, current in zip(levels, levels[1:]):
                self.assertLessEqual(current - previous, 1, f"{path}: h{previous} followed by h{current}")

    def test_panel_heading_style_does_not_depend_on_the_tag(self):
        from django.conf import settings
        css = (settings.BASE_DIR / "static/css/components.css").read_text()
        self.assertIn(".tech__heading{", css)
        self.assertNotRegex(css, r"\.tech[^{]*\bh[34]\b")          # styled by class, so the tag can change without a visual change

