from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import Brand, ProductCategory


class ProductCategoryViewSet(SnippetViewSet):
    model = ProductCategory
    icon = "list-ul"
    menu_label = "Products"
    menu_order = 100
    add_to_admin_menu = True
    list_display = ["name_en", "name_ar", "slug", "sort_order"]
    search_fields = ["name_en", "name_ar"]


class BrandViewSet(SnippetViewSet):
    model = Brand
    icon = "tag"
    menu_label = "Brands"
    menu_order = 110
    add_to_admin_menu = True
    # Brand has a single `name` field (no `name_ar`). An Arabic brand name needs a new
    # field and migration. Country of origin is not shown anywhere (client decision).
    list_display = ["name", "slug", "sort_order"]
    search_fields = ["name"]


register_snippet(ProductCategoryViewSet)
register_snippet(BrandViewSet)
