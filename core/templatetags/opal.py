from django import template
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
import re

from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from core import i18n

register = template.Library()


@register.filter
def tr(obj, field):
    """{{ obj|tr:"name" }} → obj.name_<lang>, falling back to English."""
    return i18n.tr(obj, field)


@register.simple_tag(takes_context=True)
def T(context, en, ar):
    """Inline bilingual UI string: {% T "Home" "الرئيسية" %}"""
    return ar if context.get("lang") == "ar" else en


@register.simple_tag
def lurl(path):
    return i18n.lang_url(path)


@register.simple_tag
def icon(name):
    if not name:
        return ""
    return mark_safe(get_template(f"includes/icons/{name}.svg").render())


@register.simple_tag
def cat_icon(slug):
    """Line icon for an equipment category (includes/icons/cat-<slug>.svg); empty if none exists,
    so a category added later in the admin never breaks a page."""
    try:
        return mark_safe(get_template(f"includes/icons/cat-{slug}.svg").render())
    except TemplateDoesNotExist:
        return ""


@register.filter
def brand_ids(category):
    return " ".join(s.brand.slug for s in category.supplies.all())


@register.filter
def slugpath(slug):
    """'maintenance' → '/maintenance/' for {% lurl %}."""
    return f"/{slug}/"


@register.filter
def fmt(text, name):
    """'Request a {name} quote'|fmt:brand.name — fills the {name} placeholder of a site text."""
    return str(text).replace("{name}", str(name))


_ACCENT = re.compile(r"\*([^*]+)\*")


@register.filter
def accent(text):
    """'Engineered Cooling. *Delivered with Confidence.*' → the starred words in the accent colour."""
    return mark_safe(_ACCENT.sub(r'<span class="accent">\1</span>', conditional_escape(text or "")))


@register.filter
def plain(text):
    """The same text without accent markers (titles, alt text, meta tags)."""
    return (text or "").replace("*", "")


@register.filter
def card_range(category):
    """Capacity range for a category card, exactly as stored. A value stated in tons is not shown
    (the cards carry BTU or a plain figure only); nothing is converted."""
    value = (category.capacity_range or "").strip()
    lowered = value.lower()
    if "ton" in lowered or "طن" in value or " tr" in lowered:
        return ""
    return value


# Where a service card leads when it has no page of its own: a section that exists on the home page.
SERVICE_ANCHORS = {"supply": "#products", "install": "#install", "quote": "#contact", "project": "#contractors"}


@register.simple_tag
def service_href(service):
    page = service.link_page
    if page is not None and page.live:
        return i18n.lang_url(f"/{page.slug}/")
    return SERVICE_ANCHORS.get(service.icon, "")
