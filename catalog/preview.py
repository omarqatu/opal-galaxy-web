"""Draft copy for review on brand and category pages.

DEMO holds proposed editorial wording in English and Arabic. It is NOT site content: it is
never written to the database. It is shown only when ?draft=1 is added to the address of
a page that has a draft AND the visitor is a signed-in user with access to the Wagtail
admin (or the site runs in local development with DEBUG on), under a visible "Draft
content for review" banner. Anyone else gets the normal page.

Once Omar has edited and approved a text he enters it in Wagtail Admin and its entry here
is deleted. Nothing here states a specification, capacity, model, certification, warranty,
price, stock level or delivery time. Technical data on the pages always comes from the
catalogue rows in the database, unchanged.
"""

DEMO = {
    ("brand", "carrier"): {
        "line": {
            "en": "From room units to rooftop packages, VRF systems and chilled-water equipment",
            "ar": "من وحدات الغرف إلى الوحدات المجمّعة وأنظمة VRF ومعدات المياه المبرّدة",
        },
        "intro": {
            "en": "Opal Galaxy supplies Carrier air-conditioning equipment for homes, commercial buildings and "
                  "projects. The series and models on this page are listed as Carrier publishes them for the "
                  "Gulf; the exact model, capacity and refrigerant are stated on every quotation.",
            "ar": "تورّد Opal Galaxy معدات تكييف Carrier للمنازل والمباني التجارية والمشاريع. السلاسل والطرازات "
                  "في هذه الصفحة مدرجة كما تنشرها Carrier لمنطقة الخليج، ويُذكر الطراز الدقيق والسعة ونوع غاز "
                  "التبريد في كل عرض سعر.",
        },
    },
    ("category", "vrf"): {
        "intro": {
            "en": "A VRF system connects one outdoor unit, or a group of them, to many indoor units on a single "
                  "refrigerant circuit and controls each zone separately. It suits hotels, towers, offices and "
                  "residential compounds.",
            "ar": "يربط نظام VRF وحدة خارجية واحدة أو مجموعة وحدات بعدد من الوحدات الداخلية على دائرة تبريد "
                  "واحدة، مع تحكم مستقل في كل منطقة. يناسب الفنادق والأبراج والمكاتب والمجمعات السكنية.",
        },
    },
}


def demo_for(kind, slug, lang):
    """Draft texts for one page in one language, or {} when there are none."""
    return {key: value.get(lang) or value["en"] for key, value in DEMO.get((kind, slug), {}).items()}


def may_preview(request):
    """Draft copy is for authorised reviewers: a signed-in user who can open the Wagtail admin.
    In local development (DEBUG) it is open, so designs can be checked without an account."""
    from django.conf import settings
    if settings.DEBUG:
        return True
    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated and user.has_perm("wagtailadmin.access_admin"))
