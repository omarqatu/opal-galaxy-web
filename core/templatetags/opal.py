from django import template
from django.template.loader import get_template
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


@register.filter
def brand_ids(category):
    return " ".join(s.brand.slug for s in category.supplies.all())
