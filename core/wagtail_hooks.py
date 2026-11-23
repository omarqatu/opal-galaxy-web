from wagtail.snippets.models import register_snippet
from django.db.models import F
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from .models import FieldPhoto, GalleryCategory, QuoteRequest


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


class FieldPhotoViewSet(SnippetViewSet):
    model = FieldPhoto
    icon = "image"
    menu_label = "Photos"
    list_display = ["thumbnail", "__str__", "category", "approved_for_publication", "featured",
                    "show_on_homepage", "created"]
    list_filter = ["category", "approved_for_publication", "featured", "show_on_homepage"]
    search_fields = ["title_en", "title_ar", "caption_en", "caption_ar", "alt_en", "alt_ar", "image__title"]
    list_per_page = 50
    ordering = [F("sort_order").asc(nulls_last=True), "-created", "-pk"]

    def get_queryset(self, request):
        return FieldPhoto.objects.select_related("image", "category").prefetch_related("image__renditions")


class GalleryCategoryViewSet(SnippetViewSet):
    model = GalleryCategory
    icon = "tag"
    menu_label = "Categories"
    list_display = ["name_en", "name_ar", "slug", "sort_order"]


class FieldGalleryGroup(SnippetViewSetGroup):
    """One admin area for the field gallery: photos and their categories."""
    items = (FieldPhotoViewSet, GalleryCategoryViewSet)
    menu_icon = "image"
    menu_label = "Field gallery"
    menu_name = "field-gallery"
    menu_order = 160


register_snippet(FieldGalleryGroup)
