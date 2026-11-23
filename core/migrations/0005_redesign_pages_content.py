"""Redesign, phase 3: new pages and Arabic language corrections for an existing site.

Same safety rules as 0003:
  * a correction replaces a phrase only where the old phrase is still present;
  * a page is created only when no page with its slug exists under the home page;
  * links from the home page to the new pages are set only while they are empty;
  * latest revisions are patched together with the live rows;
  * a database with no home page is left alone (seed_site applies this after seeding).
Nothing is deleted. Catalogue rows (models, specs) are not touched. Reversing does nothing.
"""
import json
import uuid

from django.db import migrations
from django.utils import timezone

# ---------------------------------------------------------------- language corrections
# (app, model, field, old phrase, new phrase). Decisions recorded in review/open-questions.md:
# "مجاري التكييف" for ducts, market terms kept, Latin technical terms after an Arabic noun,
# temperatures as a number with "°م".
FIXES = [
    ("catalog", "ProductCategory", "name_ar", "وحدات مخفية (Ducted)", "وحدات مخفية"),
    ("catalog", "ProductCategory", "name_ar", "وحدات مجمّعة (Package)", "وحدات مجمّعة"),
    ("catalog", "ProductCategory", "name_ar", "شيلرات ووحدات مناولة الهواء", "شيلرات ووحدات مناولة الهواء وفان كويل"),
    ("catalog", "ProductCategory", "lead_ar", "دون مجارٍ للهواء", "دون مجاري تكييف"),
    ("catalog", "ProductCategory", "lead_ar", "مجاري الهواء", "مجاري التكييف"),
    ("catalog", "KnowItem", "text_ar", "مجاري الهواء", "مجاري التكييف"),
    ("catalog", "KnowItem", "text_ar", "ويُورَّد R410A وR22 حيث", "ويُورَّد غاز R410A أو غاز R22 حيث"),
    ("catalog", "KnowItem", "text_ar", "يُذكر نوع الغاز", "يُذكر نوع غاز التبريد"),
    ("catalog", "Brand", "line_ar", "وتبريد دقيق وVRF", "وتبريد دقيق وأنظمة VRF"),
    ("catalog", "Brand", "about_ar", "الخيار خليجي الصنع", "الخيار الخليجي الصنع"),
    ("catalog", "Brand", "about_ar", "أرضية-سقفية", "أرضية – سقفية"),
    ("core", "FaqItem", "question_ar", "ما الفرق بين غازات R32", "ما الفرق بين غازات التبريد R32"),
    ("core", "FaqItem", "answer_ar", "عند حرارة خارجية 46° مئوية", "عند 46 °م خارجياً"),
    ("core", "FaqItem", "answer_ar", "المختبرة عند 35°.", "المختبرة عند 35 °م."),
    ("core", "FaqItem", "answer_ar", "R22 غاز قديم", "R22 غاز تبريد قديم"),
    ("core", "FaqItem", "answer_ar", "يُذكر نوع الغاز", "يُذكر نوع غاز التبريد"),
    ("core", "FaqItem", "answer_ar", "مستندات الاعتماد (Submittals) وكتالوجات المصنّع",
     "مستندات الاعتماد وكتالوجات الشركة المصنّعة"),
    ("core", "FaqItem", "answer_ar", "جدول الكميات (BOQ) أو مخططات التكييف على واتساب. نرد خلال",
     "جدول الكميات أو مخططات التكييف عبر واتساب، وسنوافيكم بالرد خلال"),
    ("core", "GalleryItem", "caption_ar", "وحدتان Inverter", "وحدتان بتقنية Inverter"),
    ("core", "HomePage", "about_text_ar", "تعمل الشركة حلقة وصل", "تعمل الشركة بوصفها حلقة وصل"),
    ("core", "HomePage", "contractors_lead_ar", "بصفة مورّد معتمد", "بصفة مورّد دائم"),
    ("core", "ServiceItem", "text_en", "for the seven brands", "for the brands we supply"),
    ("core", "ServiceItem", "text_ar", "للعلامات السبع", "للعلامات التجارية التي نورّدها"),
    ("core", "ServiceItem", "text_ar", "وفحص ضغط الغاز والكهرباء", "وفحص ضغط غاز التبريد والتوصيلات الكهربائية"),
    ("core", "CompanySettings", "quote_reply_en", "Fill the form or", "Fill in the form or"),
    ("core", "CompanySettings", "footer_about_ar",
     "Opal Galaxy Air Condition Trading L.L.C — شركة توريد أنظمة تكييف للمقاولين والمشاريع والفلل في دولة الإمارات.",
     "شركة Opal Galaxy لتجارة مكيفات الهواء: توريد أنظمة التكييف للمقاولين والمشاريع والفلل في دولة الإمارات."),
]

# ---------------------------------------------------------------- new pages
MAINTENANCE = {"form_label_en": "Maintenance / spare parts", "form_label_ar": "صيانة / قطع غيار", "icon": "parts"}

DUCT = {
    "slug": "duct-cleaning", "title": "AC duct cleaning",
    "fields": {
        "title_en": "AC duct cleaning", "title_ar": "تنظيف مجاري التكييف",
        "lead_en": "A dedicated service for cleaning air-conditioning ductwork. Tell us about the property and "
                   "the system, and we will confirm the scope of work with you before anything starts.",
        "lead_ar": "خدمة متخصصة لتنظيف مجاري التكييف. أخبرونا عن العقار ونظام التكييف، وسنؤكد لكم نطاق العمل "
                   "قبل البدء بأي إجراء.",
        "cta_en": "Request duct cleaning", "cta_ar": "طلب خدمة تنظيف مجاري التكييف",
        "list_title_en": "What to tell us", "list_title_ar": "ما نحتاج إلى معرفته",
        "form_value": "duct-cleaning", "form_label_en": "AC duct cleaning", "form_label_ar": "تنظيف مجاري التكييف",
        "icon": "duct-cleaning",
    },
    "items": [
        ("Type of property", "نوع العقار",
         "Villa, apartment, office, shop or another type of building.",
         "فيلا أو شقة أو مكتب أو محل تجاري أو أي نوع آخر من المباني."),
        ("Air-conditioning system", "نظام التكييف",
         "Ducted split, package unit or another ducted system, and the number of units if you know it.",
         "وحدات مخفية أو وحدات مجمّعة أو أي نظام آخر يعمل بمجاري التكييف، مع عدد الوحدات إن كان معروفاً."),
        ("Location", "الموقع",
         "The emirate and the area, so that we can confirm whether we can serve the site.",
         "الإمارة والمنطقة، لنؤكد لكم إمكانية تقديم الخدمة في الموقع."),
        ("Access", "إمكانية الوصول",
         "Whether the ceiling has access openings to the ducts and the indoor units.",
         "هل توجد في السقف فتحات تتيح الوصول إلى المجاري والوحدات الداخلية؟"),
    ],
}

ABOUT_WHAT_EN = ("- Supply of air-conditioning equipment from the brands listed on this site\n"
                 "- Supply with installation on request\n- Maintenance and spare parts\n- AC duct cleaning\n"
                 "- Quotations for contractors and projects, prepared from a BOQ or HVAC drawings")
ABOUT_WHAT_AR = ("- توريد معدات التكييف من العلامات التجارية المعروضة في الموقع\n- التوريد مع التركيب عند الطلب\n"
                 "- الصيانة وقطع الغيار\n- تنظيف مجاري التكييف\n"
                 "- عروض أسعار للمقاولين والمشاريع، تُعَدّ استناداً إلى جدول الكميات أو مخططات التكييف")

PRIVACY = [
    ("What this policy covers", "ما تشمله هذه السياسة",
     "This page explains what information the Opal Galaxy website receives from its visitors and what it is "
     "used for. The website belongs to Opal Galaxy Air Condition Trading L.L.C, Dubai.",
     "توضّح هذه الصفحة المعلومات التي يستقبلها موقع Opal Galaxy من زوّاره وأغراض استخدامها. الموقع تابع لشركة "
     "Opal Galaxy Air Condition Trading L.L.C في دبي."),
    ("Information you send us", "المعلومات التي ترسلونها إلينا",
     "The website receives personal information only when you send the quote request form. The form contains:\n\n"
     "- Name (optional)\n- Phone number\n- Customer type (contractor, company or end user)\n"
     "- Product and brand you are asking about\n- Quantity\n- Emirate\n- Whether installation is requested\n"
     "- Your notes or project details\n\n"
     "With each request the website also records the time it was sent, the language of the page and the page "
     "it was sent from.",
     "لا يستقبل الموقع معلومات شخصية إلا عند إرسالكم نموذج طلب عرض السعر. يتضمن النموذج:\n\n"
     "- الاسم (اختياري)\n- رقم الهاتف\n- صفة العميل (مقاول أو شركة أو فرد)\n- نوع المنتج والعلامة التجارية المطلوبة\n"
     "- الكمية\n- الإمارة\n- هل يشمل الطلب التركيب\n- ملاحظاتكم أو تفاصيل المشروع\n\n"
     "ويسجّل الموقع مع كل طلب وقت إرساله ولغة الصفحة والصفحة التي أُرسل منها."),
    ("How we use it", "كيف نستخدمها",
     "We use this information to contact you about your request and to prepare a quotation.",
     "نستخدم هذه المعلومات للتواصل معكم بشأن طلبكم ولإعداد عرض السعر."),
    ("Where requests go", "أين تُحفظ الطلبات",
     "Requests are saved in the website's database, where the company's website administrators can read them, "
     "and they are passed to the company's sales team so that they can reply to you.",
     "تُحفظ الطلبات في قاعدة بيانات الموقع، ويطّلع عليها مسؤولو الموقع لدى الشركة، وتُحال إلى فريق المبيعات "
     "في الشركة للرد عليكم."),
    ("WhatsApp, phone and email", "واتساب والهاتف والبريد الإلكتروني",
     "The WhatsApp, phone and email links on this website open those services on your device. Messages and "
     "calls made through them do not pass through the website.",
     "روابط واتساب والهاتف والبريد الإلكتروني في الموقع تفتح هذه الخدمات على جهازكم، والرسائل والمكالمات التي "
     "تُجرى عبرها لا تمر عبر الموقع."),
    ("Cookies", "ملفات تعريف الارتباط",
     "The website sets one cookie, which protects the quote form against forged submissions. The website "
     "uses no advertising or analytics cookies.",
     "يضع الموقع ملف تعريف ارتباط واحداً يحمي نموذج طلب عرض السعر من الإرسال المزوَّر. لا يستخدم الموقع ملفات "
     "تعريف ارتباط إعلانية أو تحليلية."),
    ("Delivery of the website", "تقديم الموقع",
     "The website is delivered through Cloudflare, which processes technical connection data such as IP "
     "addresses in order to deliver and protect the site.",
     "يُقدَّم الموقع عبر شبكة Cloudflare، التي تعالج بيانات الاتصال التقنية مثل عناوين IP لغرض إيصال الموقع وحمايته."),
    ("Your requests", "طلباتكم بشأن بياناتكم",
     "To ask what information we hold about you, or to have it corrected or deleted, write to "
     "info@opalgalaxy.ae.",
     "للاستفسار عن المعلومات التي نحتفظ بها عنكم، أو لطلب تصحيحها أو حذفها، راسلونا على info@opalgalaxy.ae."),
]

CONTENT_PAGES = [
    {"slug": "about", "title": "About Opal Galaxy", "kind": "text",
     "title_en": "About Opal Galaxy", "title_ar": "عن Opal Galaxy", "lead": "about_first", "sections": "about"},
    {"slug": "faq", "title": "Frequently asked questions", "kind": "faq",
     "title_en": "Frequently asked questions", "title_ar": "الأسئلة الشائعة", "lead": "faq", "sections": None},
    {"slug": "contact", "title": "Contact us", "kind": "contact",
     "title_en": "Contact us", "title_ar": "تواصل معنا",
     "lead_en": "Call us, write to us on WhatsApp or send the form below.",
     "lead_ar": "يمكنكم الاتصال بنا، أو مراسلتنا عبر واتساب، أو إرسال النموذج أدناه.", "sections": None},
    {"slug": "privacy", "title": "Privacy Policy", "kind": "text",
     "title_en": "Privacy Policy", "title_ar": "سياسة الخصوصية",
     "lead_en": "What the Opal Galaxy website receives from you, and what it is used for.",
     "lead_ar": "ما يستقبله موقع Opal Galaxy منكم، وأغراض استخدامه.", "sections": "privacy"},
]


def next_path(Page, parent):
    last = (Page.objects.filter(path__startswith=parent.path, depth=parent.depth + 1)
            .order_by("-path").values_list("path", flat=True).first())
    n = int(last[-4:], 36) + 1 if last else 1
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    step = ""
    while n:
        n, r = divmod(n, 36)
        step = digits[r] + step
    return parent.path + step.rjust(4, "0")


def add_page(apps, model_name, home, slug, title, fields):
    """Create a published child page of the home page, or return the existing page with that slug."""
    Page = apps.get_model("wagtailcore", "Page")
    Model = apps.get_model("core", model_name)
    existing = Page.objects.filter(path__startswith=home.path, depth=home.depth + 1, slug=slug).first()
    if existing:
        return existing, False
    ContentType = apps.get_model("contenttypes", "ContentType")
    ct, _ = ContentType.objects.get_or_create(app_label="core", model=model_name.lower())
    now = timezone.now()
    page = Model(title=title, draft_title=title, slug=slug, path=next_path(Page, home), depth=home.depth + 1,
                 numchild=0, url_path=f"{home.url_path}{slug}/", content_type=ct, live=True,
                 has_unpublished_changes=False, locale_id=home.locale_id, translation_key=uuid.uuid4(),
                 first_published_at=now, last_published_at=now, latest_revision_created_at=None, **fields)
    page.save()
    Page.objects.filter(pk=home.pk).update(numchild=home.numchild + 1)
    home.numchild += 1
    return Page.objects.get(pk=page.pk), True


def fix_language(apps):
    Revision = apps.get_model("wagtailcore", "Revision")
    for app, model, field, old, new in FIXES:
        Model = apps.get_model(app, model)
        for obj in Model.objects.filter(**{f"{field}__contains": old}):
            value = getattr(obj, field)
            if old in new and new in value:   # the old phrase is part of the new one: already corrected
                continue
            setattr(obj, field, value.replace(old, new))
            obj.save(update_fields=[field])
    # Latest revisions (home, service pages, product categories) carry the same texts.
    ids = set()
    for app, model in (("wagtailcore", "Page"), ("catalog", "ProductCategory")):
        ids.update(apps.get_model(app, model).objects.exclude(latest_revision=None)
                   .values_list("latest_revision_id", flat=True))
    for rev in Revision.objects.filter(pk__in=ids):
        text = before = json.dumps(rev.content, ensure_ascii=False)
        for _app, _model, _field, old, new in FIXES:
            esc_old, esc_new = json.dumps(old, ensure_ascii=False)[1:-1], json.dumps(new, ensure_ascii=False)[1:-1]
            if not (old in new and esc_new in text):
                text = text.replace(esc_old, esc_new)
        if text != before:
            rev.content = json.loads(text)
            rev.save(update_fields=["content"])


def apply_content(apps, schema_editor):
    HomePage = apps.get_model("core", "HomePage")
    home = HomePage.objects.first()
    if home is None:
        return
    fix_language(apps)
    home = HomePage.objects.get(pk=home.pk)
    Revision = apps.get_model("wagtailcore", "Revision")
    ServicePage = apps.get_model("core", "ServicePage")
    ServiceItem = apps.get_model("core", "ServiceItem")
    ContentSection = apps.get_model("core", "ContentSection")

    # The existing maintenance page: form label and icon (new fields, filled while empty).
    for sp in ServicePage.objects.filter(slug="maintenance", form_label_en=""):
        for f, v in MAINTENANCE.items():
            setattr(sp, f, v)
        sp.save()

    pages = {}
    page, created = add_page(apps, "ServicePage", home, DUCT["slug"], DUCT["title"], DUCT["fields"])
    pages["duct-cleaning"] = page
    if created:
        for i, (en, ar, ten, tar) in enumerate(DUCT["items"]):
            ServiceItem.objects.create(page_id=page.pk, sort_order=i, title_en=en, title_ar=ar,
                                       text_en=ten, text_ar=tar)

    paragraphs = lambda text: [p.strip() for p in (text or "").split("\n\n") if p.strip()]
    en, ar = paragraphs(home.about_text_en), paragraphs(home.about_text_ar)
    for spec in CONTENT_PAGES:
        fields = {k: spec[k] for k in ("kind", "title_en", "title_ar")}
        if spec.get("lead") == "about_first":
            fields["lead_en"], fields["lead_ar"] = (en[0] if en else ""), (ar[0] if ar else "")
        elif spec.get("lead") == "faq":
            fields["lead_en"], fields["lead_ar"] = home.faq_lead_en, home.faq_lead_ar
        else:
            fields["lead_en"], fields["lead_ar"] = spec["lead_en"], spec["lead_ar"]
        page, created = add_page(apps, "ContentPage", home, spec["slug"], spec["title"], fields)
        pages[spec["slug"]] = page
        if not created:
            continue
        sections = []
        if spec["sections"] == "about":
            # The About page repeats the company's own text from the home page; no new claims.
            if len(en) > 1:
                sections.append(("Our commitment", "التزامنا", "\n\n".join(en[1:]), "\n\n".join(ar[1:])))
            sections.append(("What we do", "ما نقدّمه", ABOUT_WHAT_EN, ABOUT_WHAT_AR))
        elif spec["sections"] == "privacy":
            sections = PRIVACY
        for i, (hen, har, ben, bar) in enumerate(sections):
            ContentSection.objects.create(page_id=page.pk, sort_order=i, heading_en=hen, heading_ar=har,
                                          body_en=ben, body_ar=bar)

    # Home page buttons to the new pages, while they point nowhere.
    rev = Revision.objects.filter(pk=home.latest_revision_id).first() if home.latest_revision_id else None
    content = rev.content if rev else {}
    for field, slug in (("duct_page", "duct-cleaning"), ("about_page", "about"), ("faq_page", "faq")):
        if getattr(home, f"{field}_id") is None:
            setattr(home, f"{field}_id", pages[slug].pk)
            if rev and not content.get(field):
                content[field] = pages[slug].pk
    home.save()
    HomeService = apps.get_model("core", "HomeService")
    for sv in HomeService.objects.filter(page=home, icon="duct-cleaning", link_page=None):
        sv.link_page_id = pages["duct-cleaning"].pk
        sv.save()
        for item in content.get("services", []) if rev else []:
            if item.get("pk") == sv.pk and not item.get("link_page"):
                item["link_page"] = sv.link_page_id
    if rev:
        rev.content = content
        rev.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_redesign_pages"),
        ("catalog", "0004_redesign_home"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]
    operations = [migrations.RunPython(apply_content, migrations.RunPython.noop)]
