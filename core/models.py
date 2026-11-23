from django.db import models
from django.shortcuts import get_object_or_404
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, path
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.models import Orderable, Page

from catalog.models import Brand, ProductCategory, bi
from .i18n import tr


# ---------------------------------------------------------------- settings
@register_setting(icon="site")
class CompanySettings(BaseGenericSetting):
    legal_name = models.CharField(max_length=120, default="Opal Galaxy Air Condition Trading L.L.C")
    short_name = models.CharField(max_length=60, default="OPAL GALAXY")
    tagline_en = models.CharField(max_length=80, blank=True)
    tagline_ar = models.CharField(max_length=80, blank=True)
    phone = models.CharField(max_length=20, help_text="International format, e.g. +971541981593")
    phone_display = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=20, help_text="Digits only, e.g. 971541981593")
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=200, blank=True)
    hours_short_en = models.CharField(max_length=120, blank=True)
    hours_short_ar = models.CharField(max_length=120, blank=True)
    hours_full_en = models.CharField(max_length=160, blank=True)
    hours_full_ar = models.CharField(max_length=160, blank=True)
    licence_en = models.CharField(max_length=160, blank=True)
    licence_ar = models.CharField(max_length=160, blank=True)
    footer_about_en = models.TextField(blank=True)
    footer_about_ar = models.TextField(blank=True)
    domain_label = models.CharField(max_length=80, blank=True, help_text="Shown in the footer")
    quote_reply_en = models.CharField(max_length=200, blank=True, help_text="Reply-time promise under the form title")
    quote_reply_ar = models.CharField(max_length=200, blank=True)
    facebook_url = models.URLField(blank=True, help_text="Leave empty to show the icon without a link")
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)

    panels = [
        MultiFieldPanel([FieldPanel("legal_name"), FieldPanel("short_name"), bi("tagline"),
                         FieldPanel("domain_label")], heading="Company"),
        MultiFieldPanel([FieldPanel("phone"), FieldPanel("phone_display"), FieldPanel("whatsapp"),
                         FieldPanel("email"), FieldPanel("address")], heading="Contact"),
        MultiFieldPanel([bi("hours_short"), bi("hours_full"), bi("licence"), bi("footer_about"),
                         bi("quote_reply")], heading="Texts"),
        MultiFieldPanel([FieldPanel("facebook_url"), FieldPanel("instagram_url"), FieldPanel("linkedin_url"),
                         FieldPanel("tiktok_url")], heading="Social media (footer icons)"),
    ]

    def social_links(self):
        return [(name, getattr(self, f"{name}_url")) for name in ("facebook", "instagram", "linkedin", "tiktok")]

    class Meta:
        verbose_name = "Company details"


# ---------------------------------------------------------------- site copy
# Short texts shared by every page: menu, buttons, quote section, footer headings.
# (group, field, English default, Arabic default). Defaults fill the texts on first use;
# from then on they are edited in the admin under Settings → Site texts.
SITE_COPY = [
    ("Menu", "nav_products", "Products", "المنتجات"),
    ("Menu", "nav_brands", "Brands", "العلامات التجارية"),
    ("Menu", "nav_contractors", "Contractors", "المقاولون والمشاريع"),
    ("Menu", "nav_services", "Services", "الخدمات"),
    ("Menu", "nav_maintenance", "Maintenance and parts", "الصيانة وقطع الغيار"),
    ("Menu", "nav_contact", "Contact", "تواصل معنا"),
    ("Menu", "nav_quote", "Request a quote", "طلب عرض سعر"),
    ("Quote section", "quote_title", "Request a project quote", "طلب عرض سعر لمشروعكم"),
    ("Quote section", "quote_whatsapp", "Send your BOQ on WhatsApp", "إرسال جدول الكميات عبر واتساب"),
    ("Quote section", "quote_email_label", "Or by email:", "أو عبر البريد الإلكتروني:"),
    ("Quote section", "quote_submit", "Send request", "إرسال الطلب"),
    ("Quote section", "quote_success", "Your request has been sent. Thank you.", "تم إرسال طلبكم، وشكراً لكم."),
    ("Quote section", "quote_error", "Please enter a phone number we can reach you on.",
     "يُرجى إدخال رقم هاتف صحيح للتواصل معكم."),
    ("Quote section", "quote_privacy", "We never share your details.", "لن تتم مشاركة بياناتكم مع أي جهة."),
    ("Footer", "footer_products", "Products", "المنتجات"),
    ("Footer", "footer_brands", "Brands", "العلامات التجارية"),
    ("Footer", "footer_services", "Services", "الخدمات"),
    ("Footer", "footer_contact", "Contact", "تواصل معنا"),
    ("Footer", "footer_hours", "Business hours", "ساعات العمل"),
    ("Footer", "footer_whatsapp", "Chat on WhatsApp", "تواصل عبر واتساب"),
    ("Footer", "footer_faq", "Frequently asked questions", "الأسئلة الشائعة"),
    ("Footer", "footer_privacy", "Privacy Policy", "سياسة الخصوصية"),
]


@register_setting(icon="edit")
class SiteCopy(BaseGenericSetting):
    class Meta:
        verbose_name = "Site texts"


for _group, _name, _en, _ar in SITE_COPY:
    SiteCopy.add_to_class(f"{_name}_en", models.CharField(f"{_name} (EN)", max_length=200, default=_en))
    SiteCopy.add_to_class(f"{_name}_ar", models.CharField(f"{_name} (AR)", max_length=200, default=_ar))
SiteCopy.panels = [
    MultiFieldPanel([bi(n) for g, n, _e, _a in SITE_COPY if g == group], heading=group)
    for group in dict.fromkeys(g for g, *_ in SITE_COPY)
]


# ---------------------------------------------------------------- home page
class HomePage(RoutablePageMixin, Page):
    """The home page, plus the product and brand pages served under it."""
    max_count = 1
    parent_page_types = ["wagtailcore.Page"]

    seo_title_en = models.CharField(max_length=160, blank=True)
    seo_title_ar = models.CharField(max_length=160, blank=True)
    meta_description_en = models.TextField(blank=True)
    meta_description_ar = models.TextField(blank=True)

    hero_title_en = models.CharField(max_length=160)
    hero_title_ar = models.CharField(max_length=160, blank=True)
    hero_lead_en = models.TextField(blank=True)
    hero_lead_ar = models.TextField(blank=True)
    hero_image = models.ForeignKey("wagtailimages.Image", null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="+")
    hero_alt_en = models.CharField(max_length=200, blank=True)
    hero_alt_ar = models.CharField(max_length=200, blank=True)
    hero_caption_en = models.CharField(max_length=120, blank=True)
    hero_caption_ar = models.CharField(max_length=120, blank=True)
    hero_subcaption_en = models.CharField(max_length=120, blank=True)
    hero_subcaption_ar = models.CharField(max_length=120, blank=True)
    hero_cta_primary_en = models.CharField(max_length=80, blank=True, help_text="Button to the equipment section")
    hero_cta_primary_ar = models.CharField(max_length=80, blank=True)
    hero_cta_secondary_en = models.CharField(max_length=80, blank=True, help_text="Button to the quote form")
    hero_cta_secondary_ar = models.CharField(max_length=80, blank=True)

    products_title_en = models.CharField(max_length=120, default="Products")
    products_title_ar = models.CharField(max_length=120, blank=True)
    products_lead_en = models.TextField(blank=True)
    products_lead_ar = models.TextField(blank=True)
    brands_title_en = models.CharField(max_length=120, default="Brands we supply")
    brands_title_ar = models.CharField(max_length=120, blank=True)
    brands_lead_en = models.TextField(blank=True)
    brands_lead_ar = models.TextField(blank=True)
    contractors_title_en = models.CharField(max_length=160, blank=True)
    contractors_title_ar = models.CharField(max_length=160, blank=True)
    contractors_lead_en = models.TextField(blank=True)
    contractors_lead_ar = models.TextField(blank=True)
    contractors_cta_en = models.CharField(max_length=80, blank=True)
    contractors_cta_ar = models.CharField(max_length=80, blank=True)
    contractors_image = models.ForeignKey("wagtailimages.Image", null=True, blank=True,
                                          on_delete=models.SET_NULL, related_name="+")
    contractors_image_alt_en = models.CharField(max_length=200, blank=True)
    contractors_image_alt_ar = models.CharField(max_length=200, blank=True)
    services_title_en = models.CharField(max_length=160, blank=True)
    services_title_ar = models.CharField(max_length=160, blank=True)
    services_lead_en = models.TextField(blank=True)
    services_lead_ar = models.TextField(blank=True)
    duct_title_en = models.CharField(max_length=160, blank=True)
    duct_title_ar = models.CharField(max_length=160, blank=True)
    duct_text_en = models.TextField(blank=True)
    duct_text_ar = models.TextField(blank=True)
    duct_cta_en = models.CharField(max_length=80, blank=True)
    duct_cta_ar = models.CharField(max_length=80, blank=True)
    duct_page = models.ForeignKey("wagtailcore.Page", null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name="+", help_text="Empty: the button leads to the quote form")
    install_title_en = models.CharField(max_length=160, blank=True)
    install_title_ar = models.CharField(max_length=160, blank=True)
    install_lead_en = models.TextField(blank=True)
    install_lead_ar = models.TextField(blank=True)
    install_link_en = models.CharField(max_length=200, blank=True, help_text="Link text to the maintenance page")
    install_link_ar = models.CharField(max_length=200, blank=True)
    projects_title_en = models.CharField(max_length=120, blank=True)
    projects_title_ar = models.CharField(max_length=120, blank=True)
    projects_lead_en = models.TextField(blank=True)
    projects_lead_ar = models.TextField(blank=True)
    about_title_en = models.CharField(max_length=120, blank=True)
    about_title_ar = models.CharField(max_length=120, blank=True)
    about_text_en = models.TextField(blank=True, help_text="Blank line between paragraphs")
    about_text_ar = models.TextField(blank=True)
    about_cta_en = models.CharField(max_length=80, blank=True)
    about_cta_ar = models.CharField(max_length=80, blank=True)
    about_page = models.ForeignKey("wagtailcore.Page", null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="+", help_text="Empty: no button is shown")
    faq_title_en = models.CharField(max_length=120, blank=True)
    faq_title_ar = models.CharField(max_length=120, blank=True)
    faq_lead_en = models.TextField(blank=True)
    faq_lead_ar = models.TextField(blank=True)
    faq_cta_en = models.CharField(max_length=80, blank=True)
    faq_cta_ar = models.CharField(max_length=80, blank=True)
    faq_page = models.ForeignKey("wagtailcore.Page", null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="+", help_text="Empty: no button is shown")

    content_panels = Page.content_panels + [
        MultiFieldPanel([bi("hero_title"), bi("hero_lead"), FieldPanel("hero_image"), bi("hero_alt"),
                         bi("hero_caption"), bi("hero_subcaption"), bi("hero_cta_primary"),
                         bi("hero_cta_secondary")], heading="Hero"),
        InlinePanel("facts", heading="Facts strip", label="Fact"),
        MultiFieldPanel([bi("products_title"), bi("products_lead")], heading="Products section"),
        MultiFieldPanel([bi("brands_title"), bi("brands_lead")], heading="Brands section"),
        MultiFieldPanel([bi("contractors_title"), bi("contractors_lead"), bi("contractors_cta"),
                         FieldPanel("contractors_image"), bi("contractors_image_alt")],
                        heading="Contractors section"),
        InlinePanel("contractor_points", heading="Contractor points", label="Point"),
        MultiFieldPanel([bi("services_title"), bi("services_lead")], heading="Services section"),
        InlinePanel("services", heading="Services", label="Service"),
        MultiFieldPanel([bi("duct_title"), bi("duct_text"), bi("duct_cta"), FieldPanel("duct_page")],
                        heading="Duct cleaning feature"),
        MultiFieldPanel([bi("install_title"), bi("install_lead"), bi("install_link")], heading="Installation section"),
        InlinePanel("install_steps", heading="Installation steps", label="Step"),
        MultiFieldPanel([bi("projects_title"), bi("projects_lead")], heading="Gallery section"),
        InlinePanel("gallery", heading="Gallery photos", label="Photo"),
        MultiFieldPanel([bi("about_title"), bi("about_text"), bi("about_cta"), FieldPanel("about_page")],
                        heading="About"),
        MultiFieldPanel([bi("faq_title"), bi("faq_lead"), bi("faq_cta"), FieldPanel("faq_page")],
                        heading="FAQ section"),
        InlinePanel("faqs", heading="Questions", label="Question"),
    ]
    promote_panels = Page.promote_panels + [
        MultiFieldPanel([bi("seo_title"), bi("meta_description")], heading="Bilingual SEO"),
    ]

    def home_faqs(self):
        """Questions shown on the home page; every question stays on the FAQ page."""
        return [f for f in self.faqs.all() if f.featured]

    def about_paragraphs(self):
        return [p.strip() for p in tr(self, "about_text").split("\n\n") if p.strip()]

    @path("")
    def home(self, request):
        return self.render(request, context_overrides={"page_kind": "home"})

    @path("products/<slug:slug>/")
    def product(self, request, slug):
        category = get_object_or_404(ProductCategory.objects.live(), slug=slug)
        return self.render(request, template="catalog/category.html", context_overrides={
            "page_kind": "category", "category": category,
            "supplies": category.supplies.select_related("brand").order_by("brand__sort_order"),
            "all_categories": ProductCategory.objects.live(),
        })

    @path("brands/<slug:slug>/")
    def brand(self, request, slug):
        brand = get_object_or_404(Brand, slug=slug)
        supplies = brand.live_supplies().select_related("category").order_by("category__sort_order")
        return self.render(request, template="catalog/brand.html", context_overrides={
            "page_kind": "brand", "brand": brand, "supplies": supplies,
            "all_brands": Brand.objects.all(),
        })


class _Bi(Orderable):
    class Meta:
        abstract = True
        ordering = ["sort_order"]


class HomeFact(_Bi):
    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="facts")
    title_en = models.CharField(max_length=120)
    title_ar = models.CharField(max_length=120, blank=True)
    text_en = models.CharField(max_length=200, blank=True)
    text_ar = models.CharField(max_length=200, blank=True)
    panels = [bi("title"), bi("text")]


class ContractorPoint(_Bi):
    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="contractor_points")
    title_en = models.CharField(max_length=120)
    title_ar = models.CharField(max_length=120, blank=True)
    text_en = models.CharField(max_length=240, blank=True)
    text_ar = models.CharField(max_length=240, blank=True)
    panels = [bi("title"), bi("text")]


SERVICE_ICONS = [
    ("supply", "Equipment supply"), ("install", "Installation"), ("parts", "Maintenance and spare parts"),
    ("duct-cleaning", "Duct cleaning"), ("quote", "Project quotations"), ("project", "Project support"),
]


class HomeService(_Bi):
    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="services")
    icon = models.CharField(max_length=20, choices=SERVICE_ICONS, blank=True)
    title_en = models.CharField(max_length=120)
    title_ar = models.CharField(max_length=120, blank=True)
    text_en = models.CharField(max_length=240, blank=True)
    text_ar = models.CharField(max_length=240, blank=True)
    link_page = models.ForeignKey("wagtailcore.Page", null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name="+", help_text="Empty: the card is not a link")
    panels = [FieldPanel("icon"), bi("title"), bi("text"), FieldPanel("link_page")]


class InstallStep(_Bi):
    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="install_steps")
    title_en = models.CharField(max_length=120)
    title_ar = models.CharField(max_length=120, blank=True)
    text_en = models.CharField(max_length=240, blank=True)
    text_ar = models.CharField(max_length=240, blank=True)
    panels = [bi("title"), bi("text")]


class GalleryItem(_Bi):
    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="gallery")
    image = models.ForeignKey("wagtailimages.Image", on_delete=models.CASCADE, related_name="+")
    alt_en = models.CharField(max_length=200, blank=True)
    alt_ar = models.CharField(max_length=200, blank=True)
    caption_en = models.CharField(max_length=120, blank=True)
    caption_ar = models.CharField(max_length=120, blank=True)
    subcaption_en = models.CharField(max_length=120, blank=True)
    subcaption_ar = models.CharField(max_length=120, blank=True)
    panels = [FieldPanel("image"), bi("alt"), bi("caption"), bi("subcaption")]


class FaqItem(_Bi):
    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="faqs")
    question_en = models.CharField(max_length=200)
    question_ar = models.CharField(max_length=200, blank=True)
    answer_en = models.TextField()
    answer_ar = models.TextField(blank=True)
    featured = models.BooleanField("Show on the home page", default=True)
    panels = [bi("question"), bi("answer"), FieldPanel("featured")]


# ---------------------------------------------------------------- service page
class ServicePage(Page):
    parent_page_types = ["core.HomePage"]
    subpage_types = []

    title_en = models.CharField(max_length=160)
    title_ar = models.CharField(max_length=160, blank=True)
    lead_en = models.TextField(blank=True)
    lead_ar = models.TextField(blank=True)
    cta_en = models.CharField(max_length=120, blank=True)
    cta_ar = models.CharField(max_length=120, blank=True)
    list_title_en = models.CharField(max_length=120, blank=True)
    list_title_ar = models.CharField(max_length=120, blank=True)
    form_value = models.CharField(max_length=40, default="maintenance",
                                  help_text="Value pre-selected in the quote form on this page")

    content_panels = Page.content_panels + [
        bi("title"), bi("lead"), bi("cta"), bi("list_title"), FieldPanel("form_value"),
        InlinePanel("items", heading="What is covered", label="Item"),
    ]

    def get_context(self, request, *args, **kwargs):
        ctx = super().get_context(request, *args, **kwargs)
        ctx["page_kind"] = "service"
        return ctx


class ServiceItem(_Bi):
    page = ParentalKey(ServicePage, on_delete=models.CASCADE, related_name="items")
    title_en = models.CharField(max_length=120)
    title_ar = models.CharField(max_length=120, blank=True)
    text_en = models.TextField(blank=True)
    text_ar = models.TextField(blank=True)
    panels = [bi("title"), bi("text")]


# ---------------------------------------------------------------- quote requests
class QuoteRequest(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=40)
    customer_type = models.CharField(max_length=20, blank=True)
    product = models.CharField(max_length=120, blank=True)
    brand = models.CharField(max_length=80, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    emirate = models.CharField(max_length=40, blank=True)
    installation = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    language = models.CharField(max_length=2, default="en")
    source_page = models.CharField(max_length=200, blank=True)
    forwarded = models.BooleanField(default=False, help_text="Sent to the n8n webhook")

    panels = [FieldPanel(f) for f in ("name", "phone", "customer_type", "product", "brand", "quantity",
                                      "emirate", "installation", "notes", "language", "source_page", "forwarded")]

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.created:%Y-%m-%d %H:%M} · {self.name or self.phone} · {self.product or '-'}"
