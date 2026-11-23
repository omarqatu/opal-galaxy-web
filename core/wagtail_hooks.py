from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import GalleryCategory, QuoteRequest


class QuoteRequestViewSet(SnippetViewSet):
    model = QuoteRequest
    icon = "mail"
    menu_label = "Quote requests"
    menu_order = 150
    add_to_admin_menu = True
    list_display = ["created", "name", "phone", "product", "brand", "quantity", "emirate", "forwarded"]
    list_filter = ["product", "emirate", "installation", "forwarded"]
    search_fields = ["name", "phone", "notes"]


register_snippet(QuoteRequestViewSet)


class GalleryCategoryViewSet(SnippetViewSet):
    model = GalleryCategory
    icon = "image"
    menu_label = "Gallery categories"
    list_display = ["name_en", "name_ar", "slug", "sort_order"]


register_snippet(GalleryCategoryViewSet)
