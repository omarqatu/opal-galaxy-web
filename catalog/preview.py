"""Premium internal pages: which pages use the new templates, and draft copy for review.

REFERENCE PAGES
    The redesigned brand and category templates are switched on page by page. While the two
    reference designs are under review only Carrier and VRF systems use them; every other
    brand and category page keeps the current template.

DRAFT COPY
    DEMO holds proposed editorial wording in English and Arabic. It is NOT site content:
    it is never written to the database and is shown only when a reviewer adds ?draft=1 to
    the address of a reference page on a non-indexed (staging) site, under a visible
    "Draft content for review" banner. Once Omar has edited and approved a text he enters
    it in Wagtail Admin; this file is then deleted.

    Nothing here states a specification, capacity, model, certification, warranty, price,
    stock level or delivery time. Technical data on the pages always comes from the
    catalogue rows in the database, unchanged.
"""

PREMIUM_BRANDS = {"carrier"}
PREMIUM_CATEGORIES = {"vrf"}

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
        "cta_title": {"en": "Planning a project with Carrier equipment?",
                      "ar": "هل تخططون لمشروع بمعدات Carrier؟"},
        "cta_text": {"en": "Send your BOQ or HVAC drawings and we will prepare a quotation by model.",
                     "ar": "أرسلوا جدول الكميات أو مخططات التكييف، وسنعدّ لكم عرض سعر مفصّلاً بالطرازات."},
    },
    ("category", "vrf"): {
        "intro": {
            "en": "A VRF system connects one outdoor unit, or a group of them, to many indoor units on a single "
                  "refrigerant circuit and controls each zone separately. It suits hotels, towers, offices and "
                  "residential compounds.",
            "ar": "يربط نظام VRF وحدة خارجية واحدة أو مجموعة وحدات بعدد من الوحدات الداخلية على دائرة تبريد "
                  "واحدة، مع تحكم مستقل في كل منطقة. يناسب الفنادق والأبراج والمكاتب والمجمعات السكنية.",
        },
        "cta_title": {"en": "Need a VRF selection for your project?",
                      "ar": "هل تحتاجون إلى اختيار نظام VRF لمشروعكم؟"},
        "cta_text": {"en": "Send the drawings or the equipment schedule and we will return a quotation with "
                           "the matching models.",
                     "ar": "أرسلوا المخططات أو جدول المعدات، وسنوافيكم بعرض سعر بالطرازات المناسبة."},
    },
}


def demo_for(kind, slug, lang):
    """Draft texts for one page in one language, or {} when there are none."""
    return {key: value.get(lang) or value["en"] for key, value in DEMO.get((kind, slug), {}).items()}
