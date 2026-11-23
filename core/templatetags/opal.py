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


# ---------------------------------------------------------------- catalogue rows, for reading
# The stored strings are never changed. These helpers only split them where the catalogue text
# itself separates things (" · ", or ". " before a "Label:"), so that a long row can be laid
# out as labelled lists instead of one paragraph.
_GROUP_SPLIT = re.compile(r"\.\s+(?=[A-Z][\w &/()\-]{1,40}:\s)")
_GROUP_LABEL = re.compile(r"^([A-Z][\w &/()\-]{1,40}):\s+(.+)$", re.S)


@register.filter
def model_groups(supply):
    """[(label or "", [items…]), …] from Supply.models_text, text of every item verbatim."""
    groups = []
    for chunk in (supply.models_text or "").split(" · "):
        for piece in _GROUP_SPLIT.split(chunk):
            piece = piece.strip()
            if not piece:
                continue
            match = _GROUP_LABEL.match(piece)
            if match:
                groups.append((match.group(1), [match.group(2).strip()]))
            elif groups:
                groups[-1][1].append(piece)
            else:
                groups.append(("", [piece]))
    return groups


@register.filter
def spec_rows(supply):
    """Spec lines as stored, each flagged when it states a capacity in BTU (shown emphasised)."""
    return [{"text": line, "btu": "btu" in line.lower()} for line in supply.spec_list()]


# A model or series identifier: capitals and digits (with / - _), at least one of each, e.g. 38VT008168HTMM,
# 40VU___S-4S-TEE1, 50TCM, SGS121AE. Used only to set identifiers in a distinct style; the text is unchanged.
_MODEL_ID = re.compile(r"(?<![\w/-])(?=[A-Z0-9_/\-]*[A-Z])(?=[A-Z0-9_/\-]*\d)[A-Z0-9][A-Z0-9_/\-]{2,}(?![\w-])")


@register.filter
def mark_ids(text):
    """Wrap model identifiers in <b class="tech__id">; every other character is output as stored."""
    out, last = [], 0
    for m in _MODEL_ID.finditer(text or ""):
        out.append(conditional_escape(text[last:m.start()]))
        out.append(f'<b class="tech__id">{conditional_escape(m.group(0))}</b>')
        last = m.end()
    out.append(conditional_escape((text or "")[last:]))
    return mark_safe("".join(out))


@register.filter
def spec_parts(line):
    """A spec line split at the catalogue's own " · " separators, for laying its parts out side by side."""
    return [part for part in (line or "").split(" · ") if part]
