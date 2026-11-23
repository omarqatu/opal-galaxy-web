# Internal pages — draft copy for review

Proposed wording for the two reference pages. **Draft, not site content.** None of it is saved in the database or published. It is shown only when `?draft=1` is added to the address of a reference page on staging, under a "Draft content for review" banner, with each draft text outlined and tagged.

To use a text: edit it as you see fit and enter it in Wagtail Admin in the field named in the last column. When all texts are entered, `catalog/preview.py` (the `DEMO` block) is deleted.

The drafts state no specification, capacity, model, certification, warranty, price, stock or delivery time; a test enforces that they contain no figures and none of those words.

## Carrier brand page — `/brands/carrier/?draft=1`

| Slot | English (draft) | Arabic (draft) | Replaces / where to enter |
|---|---|---|---|
| Line above the title | From room units to rooftop packages, VRF systems and chilled-water equipment | من وحدات الغرف إلى الوحدات المجمّعة وأنظمة VRF ومعدات المياه المبرّدة | Brands → Carrier → Positioning line. Current: "For commercial projects and multi-storey buildings" |
| Introduction | Opal Galaxy supplies Carrier air-conditioning equipment for homes, commercial buildings and projects. The series and models on this page are listed as Carrier publishes them for the Gulf; the exact model, capacity and refrigerant are stated on every quotation. | تورّد Opal Galaxy معدات تكييف Carrier للمنازل والمباني التجارية والمشاريع. السلاسل والطرازات في هذه الصفحة مدرجة كما تنشرها Carrier لمنطقة الخليج، ويُذكر الطراز الدقيق والسعة ونوع غاز التبريد في كل عرض سعر. | Brands → Carrier → about. The current text says "from a 1-ton wall split…", "consultants accept without discussion" and mentions R22 series; see open questions 26 |
| Quotation band, title | Planning a project with Carrier equipment? | هل تخططون لمشروع بمعدات Carrier؟ | No field yet. Without the draft the band shows Settings → Site texts → quote_title |
| Quotation band, text | Send your BOQ or HVAC drawings and we will prepare a quotation by model. | أرسلوا جدول الكميات أو مخططات التكييف، وسنعدّ لكم عرض سعر مفصّلاً بالطرازات. | No field yet. Without the draft the band shows Company details → quote_reply |

To confirm before publishing: "as Carrier publishes them for the Gulf" is true for the imported rows (window, package, VRF, chillers) and unconfirmed for the older rows (wall, ducted, cassette, floor standing), which are still on hold in `review/questions.md` (questions 10–14).

## VRF systems category page — `/products/vrf/?draft=1`

| Slot | English (draft) | Arabic (draft) | Replaces / where to enter |
|---|---|---|---|
| Introduction | A VRF system connects one outdoor unit, or a group of them, to many indoor units on a single refrigerant circuit and controls each zone separately. It suits hotels, towers, offices and residential compounds. | يربط نظام VRF وحدة خارجية واحدة أو مجموعة وحدات بعدد من الوحدات الداخلية على دائرة تبريد واحدة، مع تحكم مستقل في كل منطقة. يناسب الفنادق والأبراج والمكاتب والمجمعات السكنية. | Products → VRF systems → lead |
| Quotation band, title | Need a VRF selection for your project? | هل تحتاجون إلى اختيار نظام VRF لمشروعكم؟ | No field yet (as above) |
| Quotation band, text | Send the drawings or the equipment schedule and we will return a quotation with the matching models. | أرسلوا المخططات أو جدول المعدات، وسنوافيكم بعرض سعر بالطرازات المناسبة. | No field yet (as above) |

## New CMS fields — only if the page-specific band wording is wanted

Everything else on the two pages already comes from existing Wagtail fields. The quotation band is the one place where a page-specific text would need new fields:

- Option A (no schema change): the band keeps the existing site-wide texts (quote title and reply line).
- Option B (four fields in Settings → Site texts): `brand_band_title`, `brand_band_text`, `cat_band_title`, `cat_band_text`, with `{name}` for the brand or category, e.g. "Planning a project with {name} equipment?".

## Content seen on the reference pages that needs Omar's attention (not changed)

- Carrier rows that are not from the imported catalogue still print tons in their specification lines ("1 – 3 ton", "1 – 15 ton", "2 – 4 ton", "3 – 5 ton"). They are catalogue rows on hold and are shown as stored.
- "4 – 80 HP per system" is the stored VRF range; it is shown as stored on both pages.
- The current Carrier introduction and positioning line (see above).
- No manufacturer logo is uploaded for any brand; the pages show brand names in type.
