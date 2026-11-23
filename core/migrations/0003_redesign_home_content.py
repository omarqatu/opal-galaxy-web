"""Redesign, phase 2: write the approved home page copy into an existing site.

Rules, so that nothing the operator edited is ever overwritten:
  * an existing text is replaced only while it still equals the old text listed here;
  * a new field is filled only while it is empty;
  * list items (contractor points, process steps) change only while they are the old set;
  * the page's latest revision is patched the same way, so the admin editor shows what
    the public site shows;
  * a database with no home page is left alone (seed_site loads seed/opal.json instead).
Reversing the migration does nothing.
"""
from django.db import migrations

OLD_EMAIL, NEW_EMAIL = "opalgalaxyac@gmail.com", "info@opalgalaxy.ae"

# field: (old value or None for a new field, new value)
TEXTS = {
    "hero_title_en": ("Air conditioning, supplied at project scale",
                      "Engineered Cooling. Delivered with Confidence."),
    "hero_title_ar": ("توريد أنظمة التكييف بكميات المشاريع", "تكييف بمعايير هندسية، وتنفيذ جدير بالثقة"),
    "hero_lead_en": (
        "Dubai-based supplier of split, ducted, cassette, package and VRF systems, chillers and air handling "
        "units for contractors, companies and villas. Seven brands, one quote. Delivery across the UAE, "
        "installation on request.",
        "Premium HVAC supply, installation and project support for commercial, residential and industrial "
        "developments across the UAE."),
    "hero_lead_ar": (
        "شركة متخصصة في دبي بتوريد الوحدات المنفصلة والمخفية والكاسيت والمجمّعة وأنظمة VRF والشيلرات ووحدات "
        "مناولة الهواء للمقاولين والشركات وأصحاب الفلل. سبع علامات تجارية في عرض سعر واحد، مع التوصيل إلى جميع "
        "الإمارات والتركيب عند الطلب.",
        "حلول عالية الجودة لتوريد أنظمة التكييف وتركيبها ودعم المشاريع التجارية والسكنية والصناعية في مختلف "
        "أنحاء دولة الإمارات."),
    "hero_cta_primary_en": (None, "Explore HVAC Solutions"),
    "hero_cta_primary_ar": (None, "استكشاف حلول التكييف"),
    "hero_cta_secondary_en": (None, "Request a Project Quote"),
    "hero_cta_secondary_ar": (None, "طلب عرض سعر لمشروعكم"),
    "hero_caption_en": ("Rooftop package units", ""),
    "hero_caption_ar": ("وحدات مجمّعة على سطح مبنى تجاري", ""),
    "hero_subcaption_en": ("Supplied at project scale · Dubai", ""),
    "hero_subcaption_ar": ("توريد بكميات المشاريع · دبي", ""),
    "products_title_en": ("Products", "Equipment categories"),
    "products_title_ar": ("المنتجات", "فئات المعدات"),
    "products_lead_en": (
        "Ten equipment types, each with a page that explains where it fits and which of our brands make it.",
        "A wide range of equipment types, each with a page that explains where it fits and which of our "
        "brands make it."),
    "products_lead_ar": (
        "عشرة أنواع من المعدات، لكل منها صفحة توضح أين تناسب وأي علاماتنا التجارية تصنّعها.",
        "مجموعة واسعة من أنواع المعدات، لكل منها صفحة توضّح مجالات استخدامها والعلامات التجارية التي نورّدها منها."),
    "contractors_title_ar": ("شريك التوريد خلف برنامج مشروعك", "شريككم في التوريد على امتداد برنامج المشروع"),
    "contractors_cta_en": (None, "Send your BOQ"),
    "contractors_cta_ar": (None, "إرسال جدول الكميات"),
    "services_title_en": (None, "Our services"),
    "services_title_ar": (None, "خدماتنا"),
    "services_lead_en": (None, "Supply, installation and aftercare for air-conditioning systems, for single "
                               "orders and complete projects."),
    "services_lead_ar": (None, "توريد أنظمة التكييف وتركيبها وخدمات ما بعد البيع، للطلبات الفردية والمشاريع المتكاملة."),
    "duct_title_en": (None, "AC duct cleaning"),
    "duct_title_ar": (None, "تنظيف مجاري التكييف"),
    "duct_text_en": (None, "Duct cleaning is offered as a dedicated service. Tell us about the property and "
                           "we will get back to you with the details."),
    "duct_text_ar": (None, "نقدّم تنظيف مجاري التكييف خدمةً مستقلة. أخبرونا عن العقار، وسنوافيكم بالتفاصيل."),
    "duct_cta_en": (None, "Ask about duct cleaning"),
    "duct_cta_ar": (None, "الاستفسار عن تنظيف مجاري التكييف"),
    "install_title_en": ("Supply with installation for villas and shops", "From consultation to handover"),
    "install_title_ar": ("التوريد مع التركيب للفلل والمحال التجارية", "من الاستشارة إلى التسليم"),
    "install_link_en": ("Scheduled maintenance and original spare parts for every brand we supply →",
                        "Scheduled maintenance and original spare parts for every brand we supply"),
    "install_link_ar": ("الصيانة الدورية وقطع الغيار الأصلية لجميع العلامات التي نورّدها ←",
                        "الصيانة الدورية وقطع الغيار الأصلية لجميع العلامات التجارية التي نورّدها"),
    "about_cta_en": (None, "More about Opal Galaxy"),
    "about_cta_ar": (None, "المزيد عن Opal Galaxy"),
    "faq_title_ar": ("أسئلة شائعة", "الأسئلة الشائعة"),
    "faq_cta_en": (None, "All questions"),
    "faq_cta_ar": (None, "جميع الأسئلة"),
}

# Process steps: titles only; the descriptions stay as they are.
STEP_TITLES = {
    "Visit and sizing": ("Project consultation and site assessment", "استشارة المشروع ومعاينة الموقع"),
    "Supply and install": ("Equipment supply and installation", "توريد المعدات وتركيبها"),
    "Commissioning and handover": ("Testing, commissioning and handover", "الاختبار والتشغيل والتسليم"),
}

OLD_POINT_TITLES = ["Volume quote within one working day", "Staged deliveries",
                    "Consultant and owner paperwork", "Installation or supervision when needed"]
POINTS = [
    ("Project quotations", "عروض أسعار المشاريع",
     "Prepared from your BOQ or HVAC drawings, with alternatives from two brands on request.",
     "تُعَدّ استناداً إلى جدول الكميات أو مخططات التكييف، مع تقديم بدائل من علامتين تجاريتين عند الطلب."),
    ("BOQ support", "دعم جداول الكميات",
     "We review the bill of quantities and match its items to models from the brands we supply.",
     "نراجع جدول الكميات ونطابق بنوده مع طرازات العلامات التجارية التي نورّدها."),
    ("Technical documentation", "المستندات الفنية",
     "Submittals, compliance certificates and manufacturer catalogues for the consultant.",
     "مستندات الاعتماد وشهادات المطابقة وكتالوجات الشركات المصنّعة لتقديمها إلى الاستشاري."),
    ("Equipment supply", "توريد المعدات",
     "Units from the brands listed on this site, quoted by exact model, capacity and refrigerant.",
     "وحدات من العلامات التجارية المعروضة في الموقع، تُسعَّر بالطراز والسعة ونوع غاز التبريد."),
    ("Scheduled delivery", "التوريد وفق جدول زمني",
     "Deliveries follow the site programme, on the terms agreed in the quotation.",
     "يجري التوريد وفق برنامج الموقع، وبالشروط المتفق عليها في عرض السعر."),
    ("Installation and commissioning", "التركيب والتشغيل",
     "Our team installs, or supervises yours through commissioning and handover.",
     "يتولى فريقنا التركيب، أو يشرف على فريقكم حتى التشغيل والتسليم."),
    ("Warranty documentation", "مستندات الضمان",
     "Warranty cards issued in the project name.", "بطاقات ضمان تصدر باسم المشروع."),
]

# (icon, title EN, title AR, text EN, text AR, slug of the page it links to or None)
SERVICES = [
    ("supply", "HVAC supply", "توريد أنظمة التكييف",
     "Split, ducted, cassette, package and VRF systems, chillers and air handling units.",
     "الوحدات المنفصلة والمخفية والكاسيت والمجمّعة وأنظمة VRF والشيلرات ووحدات مناولة الهواء.", None),
    ("install", "Installation", "التركيب",
     "Supply with installation on request, through commissioning and handover.",
     "التوريد مع التركيب عند الطلب، حتى التشغيل والتسليم.", None),
    ("parts", "Maintenance and spare parts", "الصيانة وقطع الغيار",
     "Scheduled maintenance and original spare parts for the brands we supply.",
     "صيانة دورية وقطع غيار أصلية للعلامات التجارية التي نورّدها.", "maintenance"),
    ("duct-cleaning", "AC duct cleaning", "تنظيف مجاري التكييف",
     "A dedicated service for cleaning air-conditioning ductwork.", "خدمة متخصصة لتنظيف مجاري التكييف.", None),
    ("quote", "Project quotations", "عروض أسعار المشاريع",
     "Quotations prepared from your BOQ or HVAC drawings.",
     "عروض أسعار تُعَدّ استناداً إلى جدول الكميات أو مخططات التكييف.", None),
    ("project", "Contractor and commercial project support", "دعم المقاولين والمشاريع التجارية",
     "Documentation and deliveries coordinated with the site programme.",
     "مستندات وتوريد منسَّقان مع برنامج الموقع.", None),
]

# Genuine job photos (by the title seed_site gave them) for the hero and the contractors section.
OLD_HERO_IMAGE = "Home hero"
HERO_IMAGE = ("Gallery: Two inverter condensers beside a villa",
              "Two outdoor air-conditioning units installed beside a villa",
              "وحدتان خارجيتان للتكييف مركّبتان بجانب فيلا")
OLD_HERO_ALT = ("Rooftop package air-conditioning units on a commercial building in Dubai",
                "وحدات تكييف مجمّعة على سطح مبنى تجاري في دبي")
CONTRACTORS_IMAGE = ("Gallery: Crane lifting a package unit onto a roof",
                     "Crane lifting a package unit onto a roof", "رافعة ترفع وحدة مجمّعة إلى السطح")


def child(obj, fields):
    data = {"pk": obj.pk, "sort_order": obj.sort_order, "page": obj.page_id}
    data.update({f: getattr(obj, f) for f in fields})
    return data


def apply_content(apps, schema_editor):
    HomePage = apps.get_model("core", "HomePage")
    home = HomePage.objects.first()
    if home is None:
        return
    Revision = apps.get_model("wagtailcore", "Revision")
    Page = apps.get_model("wagtailcore", "Page")
    Image = apps.get_model("wagtailimages", "Image")
    rev = Revision.objects.filter(pk=home.latest_revision_id).first() if home.latest_revision_id else None
    content = rev.content if rev else {}

    def put(field, old, new):
        """Guarded write to the live page and to the latest revision."""
        if (getattr(home, field) or "") == (old or ""):
            setattr(home, field, new)
        if rev and (content.get(field) or "") == (old or ""):
            content[field] = new

    for field, (old, new) in TEXTS.items():
        put(field, old, new)

    # Images: only while the hero is still the original seed image.
    hero = Image.objects.filter(title=HERO_IMAGE[0]).first()
    if hero and home.hero_image_id and home.hero_image.title == OLD_HERO_IMAGE:
        home.hero_image = hero
        if rev:
            content["hero_image"] = hero.pk
        put("hero_alt_en", OLD_HERO_ALT[0], HERO_IMAGE[1])
        put("hero_alt_ar", OLD_HERO_ALT[1], HERO_IMAGE[2])
    crane = Image.objects.filter(title=CONTRACTORS_IMAGE[0]).first()
    if crane and not home.contractors_image_id:
        home.contractors_image = crane
        if rev:
            content["contractors_image"] = crane.pk
        put("contractors_image_alt_en", None, CONTRACTORS_IMAGE[1])
        put("contractors_image_alt_ar", None, CONTRACTORS_IMAGE[2])
    home.save()

    # Process steps: new titles on the existing rows.
    InstallStep = apps.get_model("core", "InstallStep")
    for step in InstallStep.objects.filter(page=home):
        if step.title_en in STEP_TITLES:
            old = step.title_en
            step.title_en, step.title_ar = STEP_TITLES[old]
            step.save()
            for item in content.get("install_steps", []) if rev else []:
                if item.get("pk") == step.pk and item.get("title_en") == old:
                    item["title_en"], item["title_ar"] = step.title_en, step.title_ar

    # Contractor points: replaced only while they are exactly the original four.
    ContractorPoint = apps.get_model("core", "ContractorPoint")
    points = list(ContractorPoint.objects.filter(page=home).order_by("sort_order"))
    if [p.title_en for p in points] == OLD_POINT_TITLES:
        ContractorPoint.objects.filter(page=home).delete()
        new = [ContractorPoint.objects.create(page=home, sort_order=i, title_en=en, title_ar=ar,
                                              text_en=ten, text_ar=tar)
               for i, (en, ar, ten, tar) in enumerate(POINTS)]
        if rev and [i.get("title_en") for i in content.get("contractor_points", [])] == OLD_POINT_TITLES:
            content["contractor_points"] = [child(p, ("title_en", "title_ar", "text_en", "text_ar")) for p in new]

    # Services: created once, when the page has none.
    HomeService = apps.get_model("core", "HomeService")
    if not HomeService.objects.filter(page=home).exists():
        new = []
        for i, (icon, en, ar, ten, tar, slug) in enumerate(SERVICES):
            link = Page.objects.filter(slug=slug, path__startswith=home.path, live=True).first() if slug else None
            new.append(HomeService.objects.create(page=home, sort_order=i, icon=icon, title_en=en, title_ar=ar,
                                                  text_en=ten, text_ar=tar, link_page=link))
        if rev and not content.get("services"):
            content["services"] = [child(s, ("icon", "title_en", "title_ar", "text_en", "text_ar", "link_page"))
                                   for s in new]
            for item, s in zip(content["services"], new):
                item["link_page"] = s.link_page_id

    if rev:
        rev.content = content
        rev.save()

    # Company email (approved correction).
    CompanySettings = apps.get_model("core", "CompanySettings")
    CompanySettings.objects.filter(email=OLD_EMAIL).update(email=NEW_EMAIL)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_redesign_home"),
        ("wagtailcore", "0094_alter_page_locale"),
        ("wagtailimages", "0027_image_description"),
    ]
    operations = [migrations.RunPython(apply_content, migrations.RunPython.noop)]
