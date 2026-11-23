from django.conf import settings

from wagtail.models import Page

from catalog.models import Brand, ProductCategory
from .i18n import current_lang, lang_url, strip_lang


def site_context(request):
    if request.path.startswith(("/admin", "/django-admin")):
        return {}
    lang = current_lang()
    other = "en" if lang == "ar" else "ar"
    base_path = strip_lang(request.path)
    return {
        "lang": lang,
        "dir": "rtl" if lang == "ar" else "ltr",
        "other_lang": other,
        "other_lang_url": lang_url(base_path, other),
        "en_url": lang_url(base_path, "en"),
        "ar_url": lang_url(base_path, "ar"),
        "base_path": base_path,
        "home_url": lang_url("/", lang),
        "nav_categories": ProductCategory.objects.live().prefetch_related("supplies__brand"),
        "nav_brands": Brand.objects.all(),
        "site_noindex": settings.SITE_NOINDEX,
        "site_base_url": settings.SITE_BASE_URL or request.build_absolute_uri("/").rstrip("/"),
        "service_pages": _service_pages(),
        "privacy_url": _page_url("privacy", lang),
        "faq_url": _page_url("faq", lang),
        "about_url": _page_url("about", lang),
        "contact_url": _page_url("contact", lang),
        "duct_url": _page_url("duct-cleaning", lang),
        "gallery_url": _gallery_url(lang),
        "quote_sent": request.GET.get("sent") == "1",
        "quote_error": request.GET.get("sent") == "0",
    }


def _service_pages():
    from .models import ServicePage
    return ServicePage.objects.live().order_by("path")


def _page_url(slug, lang):
    """URL of a live top-level page (child of the home page) by slug, or "" until it exists."""
    if Page.objects.filter(slug=slug, depth=3, live=True).exists():
        return lang_url(f"/{slug}/", lang)
    return ""


def _gallery_url(lang):
    """URL of the published gallery page (a content page of kind "gallery"), or "" until Omar publishes one."""
    from .models import ContentPage
    slug = ContentPage.objects.live().filter(kind="gallery", depth=3).values_list("slug", flat=True).first()
    return lang_url(f"/{slug}/", lang) if slug else ""
