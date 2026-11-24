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


# A fragment after " · " that only continues the item before it, rather than naming a new one:
# "50ZPM 36 · 48 · 60", "Split 18,000 · 24,000 BTU", "50TCM A07 · D08", "SGCA 3600i · 4800i (cool & heat)".
# It starts with a bare figure (at most a one- or two-letter suffix) or is a lone short code; a fragment
# that opens with a model identifier of its own ("50TCM A07", "38VS008168HCMM") starts a new item.
_CONTINUES = re.compile(r"^(?:[\d,.]+[A-Za-z]{0,2}(?![\w/-])(?:\s.*)?|[A-Z]{1,2}\d{1,3})$", re.S)


@register.filter
def model_groups(supply):
    """[(label or "", [items…]), …] from Supply.models_text, text of every item verbatim.

    The text is cut only at the catalogue's own separators, and a fragment that merely continues
    the previous item stays attached to it (with its " · "), so no bare "48" or "60,000 BTU" is
    ever shown as if it were a model."""
    groups = []
    for chunk in (supply.models_text or "").split(" · "):
        pieces = [p.strip() for p in _GROUP_SPLIT.split(chunk) if p.strip()]
        for n, piece in enumerate(pieces):
            match = _GROUP_LABEL.match(piece)
            if match:
                groups.append((match.group(1), [match.group(2).strip()]))
            elif groups and n == 0 and groups[-1][1] and _CONTINUES.match(piece):
                groups[-1][1][-1] += " · " + piece
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
# 40VU___S-4S-TEE1, 50TCM, SGS121AE. Refrigerant names (R410A, R-134A) are not identifiers. Used only to set
# identifiers in a distinct style; the text is unchanged.
_MODEL_ID = re.compile(r"(?<![\w/-])(?!R-?\d{2,3}[A-Z]?(?![\w-]))(?=[A-Z0-9_/\-]*[A-Z])(?=[A-Z0-9_/\-]*\d)[A-Z0-9][A-Z0-9_/\-]{2,}(?![\w-])")


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


@register.simple_tag
def photo(image, widths="320 480 720"):
    """Responsive WebP renditions of a photo: {% photo g.image "320 480 720" as im %}.

    Wagtail never enlarges an image, so widths above the original collapse to the original size and
    are listed once. WebP renditions carry no EXIF data (camera, date, GPS position).
    """
    specs = [f"width-{w}|format-webp" for w in str(widths).split()]
    by_width = {}
    for rendition in image.get_renditions(*specs).values():
        by_width.setdefault(rendition.width, rendition)
    sizes = [by_width[w] for w in sorted(by_width)]
    return {"src": sizes[0].url, "width": sizes[0].width, "height": sizes[0].height,
            "srcset": ", ".join(f"{r.url} {r.width}w" for r in sizes), "largest": sizes[-1]}


@register.simple_tag
def inquiry_message(intro, items):
    """Prefilled WhatsApp text for an inquiry: the intro, then each item's heading in the page language
    as a line for the customer to complete. Descriptions are left out, empty headings are skipped,
    and with no headings the intro alone is returned."""
    headings = [h for h in (i18n.tr(item, "title").strip() for item in items) if h]
    return "\n".join([intro, ""] + [f"{h}:" for h in headings]) if headings else intro


@register.filter
def paragraphs(text):
    """Split stored plain text into its paragraphs (separated by one or more blank lines).
    Returns plain strings, so the template escapes them as usual; empty chunks are dropped."""
    return [chunk.strip() for chunk in re.split(r"\n\s*\n", (text or "").replace("\r\n", "\n")) if chunk.strip()]

