from wagtail.snippets.models import register_snippet
from django import forms
from django.db.models import F
from django.shortcuts import redirect
from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.images.permissions import permission_policy as image_permissions
from wagtail.snippets.bulk_actions.snippet_bulk_action import SnippetBulkAction
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from .models import FieldPhoto, GalleryCategory, QuoteRequest, field_gallery_collection


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

    def get_submenu_items(self):
        upload = MenuItem("Upload photos", reverse("field_gallery_upload"), icon_name="upload", order=0)
        upload.is_shown = lambda request: can_upload_field_photos(request.user)
        return [upload] + super().get_submenu_items()


register_snippet(FieldGalleryGroup)


# ---------------------------------------------------------------- bulk upload
def can_upload_field_photos(user):
    return user.has_perm("core.add_fieldphoto") and image_permissions.user_has_permission(user, "add")


def upload_field_photos(request):
    """Open Wagtail's own multi-file image upload, pointed at the Field gallery collection.

    Each image saved into that collection gets an unapproved field photo (see models.photo_for_uploaded_image),
    so file validation, size limits, duplicate detection and storage are all Wagtail's.
    """
    from django.core.exceptions import PermissionDenied
    if not can_upload_field_photos(request.user):
        raise PermissionDenied
    collection = field_gallery_collection(create=True)
    return redirect(f"{reverse('wagtailimages:add_multiple')}?collection_id={collection.pk}")


@hooks.register("register_admin_urls")
def field_gallery_urls():
    return [path("field-gallery/upload/", upload_field_photos, name="field_gallery_upload")]


# ---------------------------------------------------------------- bulk actions on the photo listing
class FieldPhotoBulkAction(SnippetBulkAction):
    """Base for actions on selected field photos. Subclasses set `values` or override values_for()."""
    models = [FieldPhoto]
    template_name = "core/admin/field_photo_bulk_action.html"
    permission = "core.change_fieldphoto"
    values = {}
    question = ""
    done = ""

    def check_perm(self, photo):
        return self.request.user.has_perm(self.permission)

    def values_for(self):
        return self.values

    def get_execution_context(self):
        return {**super().get_execution_context(), "values": self.values_for()}

    def get_context_data(self, **kwargs):
        return super().get_context_data(question=self.question, action_label=self.display_name, **kwargs)

    @classmethod
    def execute_action(cls, objects, values=None, **kwargs):
        return FieldPhoto.objects.filter(pk__in=[p.pk for p in objects]).update(**values), 0

    def get_success_message(self, num_parent_objects, num_child_objects):
        return f"{num_parent_objects} {self.done}"


class ApproveBulkAction(FieldPhotoBulkAction):
    display_name = "Approve"
    action_type = "approve"
    aria_label = "Approve the selected photos for publication"
    action_priority = 10
    permission = "core.approve_fieldphoto"
    values = {"approved_for_publication": True}
    question = ("Approve these photos for publication? Check first that none shows an identifiable face or "
                "vehicle number plate without permission or redaction.")
    done = "photo(s) approved for publication."


class WithdrawBulkAction(FieldPhotoBulkAction):
    display_name = "Withdraw approval"
    action_type = "withdraw"
    aria_label = "Withdraw the approval of the selected photos"
    action_priority = 11
    permission = "core.approve_fieldphoto"
    values = {"approved_for_publication": False}
    question = "Withdraw approval? These photos leave the site at once; the records and files are kept."
    done = "photo(s) withdrawn from the site."


class ShowOnHomeBulkAction(FieldPhotoBulkAction):
    display_name = "Show on home"
    action_type = "home_on"
    aria_label = "Show the selected photos on the homepage"
    action_priority = 12
    values = {"show_on_homepage": True}
    question = "Mark these photos for the homepage? It shows up to eight approved photos, lowest homepage order first."
    done = "photo(s) marked for the homepage."


class HideFromHomeBulkAction(FieldPhotoBulkAction):
    display_name = "Remove from home"
    action_type = "home_off"
    aria_label = "Remove the selected photos from the homepage"
    action_priority = 13
    values = {"show_on_homepage": False}
    question = "Remove these photos from the homepage? They stay in the gallery."
    done = "photo(s) removed from the homepage."


class CategoryForm(forms.Form):
    category = forms.ModelChoiceField(queryset=GalleryCategory.objects.all(), required=False,
                                      empty_label="No category", label="Category")


class SetCategoryBulkAction(FieldPhotoBulkAction):
    display_name = "Set category"
    action_type = "set_category"
    aria_label = "Set the category of the selected photos"
    action_priority = 14
    form_class = CategoryForm
    question = "Choose the category for these photos."
    done = "photo(s) moved to the chosen category."

    def values_for(self):
        return {"category": self.cleaned_form.cleaned_data["category"]}


for _action in (ApproveBulkAction, WithdrawBulkAction, ShowOnHomeBulkAction, HideFromHomeBulkAction, SetCategoryBulkAction):
    hooks.register("register_bulk_action", _action)
