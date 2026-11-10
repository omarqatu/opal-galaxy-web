from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.models import Orderable
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
    origin_en = models.CharField(max_length=80, blank=True)
    origin_ar = models.CharField(max_length=80, blank=True)
    line_en = models.CharField("Positioning line (EN)", max_length=200, blank=True)
    line_ar = models.CharField("Positioning line (AR)", max_length=200, blank=True)
    about_en = models.TextField(blank=True)
    about_ar = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    panels = [
        FieldRowPanel([FieldPanel("name"), FieldPanel("slug"), FieldPanel("sort_order")]),
        bi("origin"), bi("line"), bi("about"),
    ]
    search_fields = [index.SearchField("name"), index.AutocompleteField("name")]

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def get_url(self, lang=None):
        return lang_url(f"/brands/{self.slug}/", lang)

    def categories(self):
        return ProductCategory.objects.filter(supplies__brand=self).distinct()


class ProductCategory(index.Indexed, ClusterableModel):
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


class KnowItem(Orderable):
    category = ParentalKey(ProductCategory, on_delete=models.CASCADE, related_name="know_items")
    title_en = models.CharField(max_length=120)
    title_ar = models.CharField(max_length=120, blank=True)
    text_en = models.TextField()
    text_ar = models.TextField(blank=True)
    panels = [bi("title"), bi("text")]


class Supply(Orderable):
    """One cell of the product × brand matrix."""
    category = ParentalKey(ProductCategory, on_delete=models.CASCADE, related_name="supplies")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="supplies")
    models_text = models.TextField("Series / models", help_text="As published by the manufacturer")
    specs = models.TextField(blank=True, help_text="One spec per line (capacity, refrigerant, efficiency…)")
    pending = models.BooleanField("Models confirmed on quote", default=False,
                                  help_text="Show 'confirmed on the quote' instead of the spec line")
    panels = [FieldPanel("brand"), FieldPanel("models_text"), FieldPanel("specs"), FieldPanel("pending")]

    class Meta(Orderable.Meta):
        constraints = [models.UniqueConstraint(fields=["category", "brand"], name="one_supply_per_cell")]

    def spec_list(self):
        return [s.strip() for s in self.specs.splitlines() if s.strip()]

