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

    panels = [
        MultiFieldPanel([FieldPanel("legal_name"), FieldPanel("short_name"), bi("tagline"),
                         FieldPanel("domain_label")], heading="Company"),
        MultiFieldPanel([FieldPanel("phone"), FieldPanel("phone_display"), FieldPanel("whatsapp"),
                         FieldPanel("email"), FieldPanel("address")], heading="Contact"),
        MultiFieldPanel([bi("hours_short"), bi("hours_full"), bi("licence"), bi("footer_about"),
                         bi("quote_reply")], heading="Texts"),
    ]

    class Meta:
        verbose_name = "Company details"


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
    faq_title_en = models.CharField(max_length=120, blank=True)
    faq_title_ar = models.CharField(max_length=120, blank=True)
    faq_lead_en = models.TextField(blank=True)
    faq_lead_ar = models.TextField(blank=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel([bi("hero_title"), bi("hero_lead"), FieldPanel("hero_image"), bi("hero_alt"),
                         bi("hero_caption"), bi("hero_subcaption")], heading="Hero"),
        InlinePanel("facts", heading="Facts strip", label="Fact"),
        MultiFieldPanel([bi("products_title"), bi("products_lead")], heading="Products section"),
        MultiFieldPanel([bi("brands_title"), bi("brands_lead")], heading="Brands section"),
        MultiFieldPanel([bi("contractors_title"), bi("contractors_lead")], heading="Contractors section"),
        InlinePanel("contractor_points", heading="Contractor points", label="Point"),
        MultiFieldPanel([bi("install_title"), bi("install_lead"), bi("install_link")], heading="Installation section"),
        InlinePanel("install_steps", heading="Installation steps", label="Step"),
        MultiFieldPanel([bi("projects_title"), bi("projects_lead")], heading="Gallery section"),
        InlinePanel("gallery", heading="Gallery photos", label="Photo"),
        MultiFieldPanel([bi("about_title"), bi("about_text")], heading="About"),
        MultiFieldPanel([bi("faq_title"), bi("faq_lead")], heading="FAQ section"),
        InlinePanel("faqs", heading="Questions", label="Question"),
    ]
    promote_panels = Page.promote_panels + [
        MultiFieldPanel([bi("seo_title"), bi("meta_description")], heading="Bilingual SEO"),
    ]

    def about_paragraphs(self):
        return [p.strip() for p in tr(self, "about_text").split("\n\n") if p.strip()]

    @path("")
    def home(self, request):
        return self.render(request, context_overrides={"page_kind": "home"})

    @path("products/<slug:slug>/")
    def product(self, request, slug):
        category = get_object_or_404(ProductCategory, slug=slug)
        return self.render(request, template="catalog/category.html", context_overrides={
            "page_kind": "category", "category": category,
            "supplies": category.supplies.select_related("brand").order_by("brand__sort_order"),
            "all_categories": ProductCategory.objects.all(),
        })

    @path("brands/<slug:slug>/")
    def brand(self, request, slug):
        brand = get_object_or_404(Brand, slug=slug)
        supplies = brand.supplies.select_related("category").order_by("category__sort_order")
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
    panels = [bi("question"), bi("answer")]


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
