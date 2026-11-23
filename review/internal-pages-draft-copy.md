# Internal pages — draft copy for review

Proposed wording for two pages (Carrier brand, VRF systems category). **Draft, not site content.** None of it is saved in the database or published.

Since the rollout every brand and category page uses the same templates; only the two pages below have draft texts, and `?draft=1` changes nothing on any other page.

How to see it: sign in to the Wagtail admin on staging, then open one of the two pages with `?draft=1` added to its address. The drafts appear under a "Draft content for review" banner, each one outlined and tagged. A visitor who is not signed in (or has no admin access) gets the normal page even with `?draft=1`. In local development the preview is open.

To use a text: edit it as you see fit and enter it in Wagtail Admin in the field named in the last column. When all texts are entered, the `DEMO` block in `catalog/preview.py` is deleted.

The drafts state no specification, capacity, model, certification, warranty, price, stock or delivery time; a test enforces that they contain no figures and none of those words.

The quotation band on both pages keeps the existing general texts (Site texts → quote_title, Company details → quote_reply). No draft is proposed for it and no new field is needed.

## Carrier brand page — `/brands/carrier/?draft=1`

| Slot | English (draft) | Arabic (draft) | Replaces / where to enter |
|---|---|---|---|
| Line above the title | From room units to rooftop packages, VRF systems and chilled-water equipment | من وحدات الغرف إلى الوحدات المجمّعة وأنظمة VRF ومعدات المياه المبرّدة | Brands → Carrier → Positioning line. Current: "For commercial projects and multi-storey buildings" |
| Introduction | Opal Galaxy supplies Carrier air-conditioning equipment for homes, commercial buildings and projects. The series and models on this page are listed as Carrier publishes them for the Gulf; the exact model, capacity and refrigerant are stated on every quotation. | تورّد Opal Galaxy معدات تكييف Carrier للمنازل والمباني التجارية والمشاريع. السلاسل والطرازات في هذه الصفحة مدرجة كما تنشرها Carrier لمنطقة الخليج، ويُذكر الطراز الدقيق والسعة ونوع غاز التبريد في كل عرض سعر. | Brands → Carrier → about. The current text says "from a 1-ton wall split…", "consultants accept without discussion" and mentions R22 series; see open questions 26 |

To confirm before publishing: "as Carrier publishes them for the Gulf" is true for the imported rows (window, package, VRF, chillers) and unconfirmed for the older rows (wall, ducted, cassette, floor standing), which are still on hold in `review/questions.md` (questions 10–14).

## VRF systems category page — `/products/vrf/?draft=1`

| Slot | English (draft) | Arabic (draft) | Replaces / where to enter |
|---|---|---|---|
| Introduction | A VRF system connects one outdoor unit, or a group of them, to many indoor units on a single refrigerant circuit and controls each zone separately. It suits hotels, towers, offices and residential compounds. | يربط نظام VRF وحدة خارجية واحدة أو مجموعة وحدات بعدد من الوحدات الداخلية على دائرة تبريد واحدة، مع تحكم مستقل في كل منطقة. يناسب الفنادق والأبراج والمكاتب والمجمعات السكنية. | Products → VRF systems → lead |

## New CMS fields

None.

## Content seen on the pages that needs Omar's attention (not changed)

- Carrier rows that are not from the imported catalogue still print tons in their specification lines ("1 – 3 ton", "1 – 15 ton", "2 – 4 ton", "3 – 5 ton"). They are catalogue rows on hold and are shown as stored.
- "4 – 80 HP per system" is the stored VRF range; it is shown as stored on both pages.
- The current Carrier introduction and positioning line (see above).
- No manufacturer logo is uploaded for any brand; the pages show brand names in type.
- Rollout: rows outside the imported catalogues (O General, Midea, Coolex, Westpoint, older Carrier rows) print tons, MBH, °C and °F in their specification lines exactly as stored ("Inverter 1.5 – 5 ton (18 – 60 MBH)", "rated to 125 °F"). Nothing was converted; the unit audit stays with Omar.
- Rollout: Daikin, LG, SKM and Trane have no catalogue rows. Their pages show the "confirmed on the quote" panel with the quotation button and no equipment list.
