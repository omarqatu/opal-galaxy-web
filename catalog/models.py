from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.template.response import TemplateResponse
from django.utils import translation
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.models import DraftStateMixin, Orderable, PreviewableMixin, RevisionMixin
from wagtail.search import index

from core.i18n import lang_url

ICON_CHOICES = [
    ("", "None"), ("window", "Window unit"), ("fc", "Floor-ceiling"), ("chill", "Chiller"),
    ("dc", "Data center"), ("parts", "Spare parts"),
]


def bi(name):
    """A pair of side-by-side panels for an *_en / *_ar field."""
    return FieldRowPanel([FieldPanel(f"{name}_en", heading=f"{name} (EN)"),
                          FieldPanel(f"{name}_ar", heading=f"{name} (AR)")])


class Brand(index.Indexed, models.Model):
    slug = models.SlugField(unique=True, help_text="Used in the URL: /brands/<slug>/")
    name = models.CharField(max_length=80)
    line_en = models.CharField("Positioning line (EN)", max_length=200, blank=True)
    line_ar = models.CharField("Positioning line (AR)", max_length=200, blank=True)
    about_en = models.TextField(blank=True)
    about_ar = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    panels = [
        FieldRowPanel([FieldPanel("name"), FieldPanel("slug"), FieldPanel("sort_order")]),
        bi("line"), bi("about"),
    ]
    search_fields = [index.SearchField("name"), index.AutocompleteField("name")]

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def get_url(self, lang=None):
        return lang_url(f"/brands/{self.slug}/", lang)

    def categories(self):
        return ProductCategory.objects.live().filter(supplies__brand=self).distinct()

    def live_supplies(self):
        """This brand's rows in published categories only (drafts never reach the public site)."""
        return self.supplies.filter(category__live=True)


class ProductCategoryQuerySet(models.QuerySet):
    def live(self):
        return self.filter(live=True)


class ProductCategory(PreviewableMixin, DraftStateMixin, RevisionMixin, index.Indexed, ClusterableModel):
    """A product type. Edits are saved as draft revisions; the public site shows only the
    published version (the database row), never a draft."""
    slug = models.SlugField(unique=True, help_text="Used in the URL: /products/<slug>/")
    name_en = models.CharField(max_length=120)
    name_ar = models.CharField(max_length=120, blank=True)
    capacity_range = models.CharField(max_length=80, blank=True, help_text="e.g. 9,000 – 36,000 BTU")
    lead_en = models.TextField(blank=True)
    lead_ar = models.TextField(blank=True)
    image = models.ForeignKey("wagtailimages.Image", null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="+")
    icon = models.CharField(max_length=20, blank=True, choices=ICON_CHOICES,
                            help_text="Shown only when there is no image")
    sort_order = models.PositiveIntegerField(default=0)

    panels = [
        FieldRowPanel([FieldPanel("slug"), FieldPanel("capacity_range"), FieldPanel("sort_order")]),
        bi("name"), bi("lead"),
        FieldRowPanel([FieldPanel("image"), FieldPanel("icon")]),
        InlinePanel("know_items", heading="Good to know before you order", label="Point"),
        InlinePanel("supplies", heading="Brands that supply this product", label="Brand"),
    ]
    search_fields = [index.SearchField("name_en"), index.SearchField("name_ar"),
                     index.AutocompleteField("name_en")]
    _revisions = GenericRelation("wagtailcore.Revision", related_query_name="productcategory")

    objects = ProductCategoryQuerySet.as_manager()

    class Meta:
        ordering = ["sort_order", "name_en"]
        verbose_name = "product category"
        verbose_name_plural = "product categories"

    def __str__(self):
        return self.name_en

    def get_url(self, lang=None):
        return lang_url(f"/products/{self.slug}/", lang)

    def brands(self):
        return [s.brand for s in self.supplies.select_related("brand").order_by("brand__sort_order")]

    @property
    def revisions(self):
        return self._revisions

    # ---- preview of a draft in the admin, with the public category template
    preview_modes = [("en", "English"), ("ar", "Arabic")]

    def get_preview_template(self, request, mode_name):
        return "catalog/category.html"

    def get_preview_context(self, request, mode_name):
        supplies = sorted(self.supplies.all(), key=lambda s: (s.brand.sort_order, s.brand.name))
        return {"request": request, "page_kind": "category", "category": self, "supplies": supplies,
                "all_categories": ProductCategory.objects.live()}

    def serve_preview(self, request, mode_name):
        # Render now, inside the language override: templates and context processors read
        # the active language.
        with translation.override("ar" if mode_name == "ar" else "en"):
            response = TemplateResponse(request, self.get_preview_template(request, mode_name),
                                        self.get_preview_context(request, mode_name))
            response.render()
        return response


class KnowItem(Orderable):
    category = ParentalKey(ProductCategory, on_delete=models.CASCADE, related_name="know_items")
    title_en = models.CharField(max_length=120)
    title_ar = models.CharField(max_length=120, blank=True)
    text_en = models.TextField()
    text_ar = models.TextField(blank=True)
    panels = [bi("title"), bi("text")]


SOURCE_TYPES = [
    ("manufacturer_catalogue", "Manufacturer catalogue"),
    ("official_site", "Official site"),
    ("distributor", "Distributor"),
    ("unknown", "Unknown"),
]


class Supply(Orderable):
    """One cell of the product × brand matrix."""
    category = ParentalKey(ProductCategory, on_delete=models.CASCADE, related_name="supplies")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="supplies")
    models_text = models.TextField("Series / models", help_text="As published by the manufacturer")
    specs = models.TextField(blank=True, help_text="One spec per line (capacity, refrigerant, efficiency…)")
    pending = models.BooleanField("Models confirmed on quote", default=False,
                                  help_text="Show 'confirmed on the quote' instead of the spec line")
    nominal_tons_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                           help_text="Manufacturer's nominal TR class, as printed. Never calculated.")
    nominal_tons_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                           help_text="Manufacturer's nominal TR class, as printed. Never calculated.")
    source = models.CharField(max_length=255, blank=True,
                              help_text='Where the data comes from, e.g. "Carrier CLK Floor Stand Feb 2023, p.4"')
    source_type = models.CharField(max_length=30, choices=SOURCE_TYPES, default="unknown")
    panels = [FieldPanel("brand"), FieldPanel("models_text"), FieldPanel("specs"), FieldPanel("pending"),
              FieldRowPanel([FieldPanel("nominal_tons_min"), FieldPanel("nominal_tons_max")]),
              FieldRowPanel([FieldPanel("source"), FieldPanel("source_type")])]

    class Meta(Orderable.Meta):
        constraints = [models.UniqueConstraint(fields=["category", "brand"], name="one_supply_per_cell")]

    def spec_list(self):
        return [s.strip() for s in self.specs.splitlines() if s.strip()]

