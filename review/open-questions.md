# Open questions — Opal Galaxy website

Maintained through the redesign (last update: design refinement, 23 Nov 2026). Catalogue questions stay in `review/questions.md`.

Each row: the exact text affected · what needs confirming · the placeholder used meanwhile. "Ahmad" = business owner; "Omar" = operator.

## All pages (header, footer, company details)

| # | Text affected | To confirm | Placeholder meanwhile |
|---|---|---|---|
| 1 | "Saturday – Thursday, 8:00 – 18:00 · Sunday closed" / "السبت – الخميس، 8:00 – 18:00 · الأحد عطلة" (About block); "Saturday – Thursday 8:00 – 18:00" (footer) | Ahmad: actual working days and hours. Saturday – Thursday already includes Sunday, so "Sunday closed" contradicts it. | Text left as it is; no `openingHours` in structured data. |
| 2 | `opalgalaxyac@gmail.com` → `info@opalgalaxy.ae` | Omar: the mailbox exists and is monitored. | New address used as approved. |
| 3 | "St152 – Port Saeed, Deira, Dubai – UAE" | Ahmad: full postal address (building, office number, P.O. Box) for the Contact page and structured data. | Current line only; no street-level fields in structured data. |
| 4 | "Dubai Department of Economy and Tourism" (Licence) | Ahmad: licence number, and whether to show it. | Current line. |
| 5 | Footer social icons | Ahmad / Omar: URLs for Facebook · Instagram · LinkedIn · TikTok (all four missing). | Icons shown without a link. |
| 6 | Brand pages for SKM, LG, Daikin, Trane | Created in Phase 1 as name-only records (Omar's decision, 23 Nov). Omar writes their positioning line, description and series in the admin. | Page shows the brand name and "Models and capacities are confirmed on the quote." |
| 7 | Brand logos | Ahmad: approved logo files and permission for each of the brands. | Brand names in type. |
| 8a | Quote form processing (validation, storage, forwarding, notifications) | Omar (23 Nov): the form stays as it is for now and will be dealt with separately. Open: who is notified of a request and how; whether the visitor gets a confirmation; whether typed data should survive a validation error. | Form unchanged. |
| 8b | Capacity units across the site | Omar audits BTU and the other units himself. New copy is written in BTU (VRF: HP with BTU where the catalogue gives it). Existing texts and imported spec lines are **not** converted or corrected in the redesign. | Existing values shown as stored. |
| 8c | Spec lines on Arabic pages (stored in English only) | Phase 3 applies option A: models and specs are shown exactly as stored, in a left-to-right technical block marked as English. Omar may still choose a display glossary or an Arabic field later; neither needs a redesign. | English technical block. |
| 8 | "We never share your details." / "لن تتم مشاركة بياناتكم مع أي جهة." | Omar: requests are forwarded to an n8n webhook when configured; confirm the sentence is still true, or reword. | Sentence kept, linked to the Privacy Policy. |

## Home

| # | Text affected | To confirm | Placeholder meanwhile |
|---|---|---|---|
| 8d | Hero image | Omar approved (23 Nov) an AI-generated rooftop image as a conceptual marketing illustration. It is not a photograph of an Opal Galaxy installation: its alt text says "Illustration", it has no caption, and it is not in the project gallery. Ahmad: real photographs as listed in the Phase 0 report, to replace it when available. | Illustration in the hero only. |
| 8e | Highlights under the hero ("HVAC supply and installation", "Maintenance and spare parts", "Project and contractor support") | They replace the three notes shown there before ("Delivery within 48 hours", "Trade pricing for contractors", "Installation on request"). Those notes are kept in the admin (Home → Facts) and the 48-hour statement remains in the FAQ. Ahmad: confirm the claims before they return to the top of the page. | Highlights shown; notes not shown. |
| 8f | Capacity on category cards | Rule (Omar, 23 Nov): never the word "ton"; a card shows the stored value only when it is in BTU or is a plain figure. Package ("3 – 100 ton") and chillers ("3 – 500 ton") therefore show the name only. "4 – 80 HP per system" is shown as stored; Omar edits it in the admin. Nothing is converted. | Stored values, tons hidden. |
| 8g | Gallery captions | Unsupported brand, capacity and site claims: "O General 5 ton", "Midea Package 15 ton", "Midea 5 ton", "Commercial compound", "Warehouse", "Private villa", "Occupied villa", "Villa under construction", "Residential project". Omar edits them in the admin (Pages → Home → Gallery photos); the redesign does not change them. | Captions shown as stored. |
| 8h | People and a vehicle plate in gallery photos | "Ducted unit delivery" (a person from behind and a readable number plate) and "Midea 5 ton" (a technician's face). Published by Omar's decision (23 Nov); Omar follows up consent or blurred replacements with Ahmad. | Photos published as they are. |
| 8i | Gallery order | The two lead photos are the first two in Pages → Home → Gallery photos. The refinement moved "Two inverter condensers beside a villa" and "Crane lifting a package unit" to the front once; reorder them in the admin at any time. | Villa units and crane lift lead. |
| 8j | Brands section text "Genuine units through authorised UAE distributors, with manufacturer warranty and original spare parts." | Ahmad: is this true for every brand listed? It reads as a distributor-relationship claim (see 13). | Text unchanged; brand tiles themselves make no partnership claim. |
| 9 | New hero: "…for commercial, residential and industrial developments across the UAE." | Ahmad: does Opal Galaxy serve industrial developments? | Text as supplied in the brief. |
| 10 | "Delivery within 48 hours — Dubai, Sharjah and Ajman. Other emirates by order size." (facts strip and FAQ) | Ahmad: is this a commitment, for which items and areas? | Kept as a small note under the hero and in the FAQ; no longer a headline band. |
| 11 | "Volume quote within one working day"; "We reply within one working day." (contractor points, quote section, FAQ, form success notice) | Ahmad: confirm the response time. | Kept in the line under the quote heading and in the FAQ. Removed from the contractors heading and from the form's success notice (now "Your request has been sent. Thank you."). |
| 12 | "Trade pricing for contractors — Volume quotes with tax invoice and manufacturer warranty" | Ahmad: confirm each element. | Kept, not emphasised. |
| 13 | "Genuine units through authorised UAE distributors, with manufacturer warranty and original spare parts." | Ahmad: true for every brand listed? | Kept. |
| 14 | "Staged deliveries — We reserve the quantity and deliver as the site progresses, no storage on your side." | Ahmad: confirm terms for scheduled delivery. | Rewritten in Phase 2 as "Scheduled delivery — Deliveries follow the site programme, on the terms agreed in the quotation." The reservation / no-storage promise is not stated until confirmed. |
| 15 | "Submittals, compliance certificates and warranty cards in the project name." | Ahmad: which documents are actually provided. | Kept, split into "Technical documentation" and "Warranty documentation". |
| 16 | "From your BOQ or HVAC drawings, with alternatives from two brands on request." | Ahmad: confirm. | Kept. |
| 17 | "Installation or supervision when needed — Our team installs, or supervises yours through commissioning and handover." | Ahmad: own installation team or subcontracted? Is commissioning offered? | Kept. |
| 18 | "built on years of supplying and installing HVAC"; "distributor pricing with the speed of a small supplier"; "on the agreed date, with a warranty card in your name" | Ahmad: founding year / years in business; confirm the three promises. | Kept unchanged (no factual changes to About). |
| 19 | Hero photo and caption "Rooftop package units · Supplied at project scale · Dubai" | Origin of the current image is unconfirmed. Decision (23 Nov): the new hero uses a genuine gallery photo in a portrait frame until Ahmad supplies new photographs. | Genuine gallery photo. |
| 20 | Gallery captions: "O General 5 ton", "Midea Package 15 ton", "Commercial compound", "Warehouse", "Private villa", "Occupied villa", "Villa under construction", "Residential project", "Twin Inverter units" | Ahmad: brand, capacity and site type for each photo; permission to show people (photos 5 and 6) and the vehicle plate (photo 5). | Neutral captions describing only what is visible. |
| 20a | Gallery approval (field gallery, PR A): each photo has "Approved for publication" in the admin | Omar: the eight existing photos stay approved by his decision (23 Nov), including photos 5 and 6 (people) and the vehicle plate noted in 20; he reviews them in the admin and unticks any that should not be shown. New photos are unapproved until ticked. | Existing eight shown as before; new uploads hidden until approved. |
| 20b | Field gallery (PR B): files of photos | Omar: (1) a photo whose approval is withdrawn leaves every page at once, but its resized file stays reachable by its direct address until the image is deleted or replaced in the admin; to redact a photo, replace the file in Images, which gives it new addresses. (2) Original uploads are now served to signed-in admin users only; copies already held by the Cloudflare cache are not purged by this change. (3) The source photos are small (675 px wide at most); larger originals would look sharper in the viewer. | Nothing changed in Cloudflare. |

| 20a | New contractor point "BOQ support — We review the bill of quantities and match its items to models from the brands we supply." | Ahmad: confirm this describes what Opal does with a BOQ. | As written. |
| 20b | New services section (HVAC supply, Installation, Maintenance and spare parts, AC duct cleaning, Project quotations, Contractor and commercial project support) | Ahmad: confirm the six services and their one-line descriptions. | As written; no prices, durations or guarantees. |
| 20c | "Duct cleaning is offered as a dedicated service. Tell us about the property and we will get back to you with the details." | Ahmad: see the Duct cleaning section below. | Button leads to the quote form until the page exists. |

## Product category pages

| # | Text affected | To confirm | Placeholder meanwhile |
|---|---|---|---|
| 21 | Ducted range "12,000-336,000" | Omar (unit audit, 8b): unit and intended wording. | Shown as stored. |
| 22 | Ranges "3 – 100 ton" (package), "3 – 500 ton" (chillers), "4 – 80 HP per system" (VRF), window "18,000 – 27,000 BTU", floor standing "36,000 – 60,000 BTU" | Omar (unit audit, 8b): ranges no longer match the imported rows (e.g. Super General window from 17400, floor standing to 120000). | Shown as stored. |
| 23 | Category product images (nine) | Decision (23 Nov): replaced by the line-icon set. Ahmad: right to use manufacturers' product images, if they are wanted back later. | Line icons (from Phase 2). |
| 24 | "Roughly 12,000 BTU per 12 – 15 m² in a UAE villa"; "A typical 4-bedroom villa takes 5 – 7 ducted units of 2 – 5 ton"; "two units handle most majlis layouts" | Ahmad: keep these rules of thumb? | Kept. |

## Brand pages

| # | Text affected | To confirm | Placeholder meanwhile |
|---|---|---|---|
| 25 | Super General: "Wall splits from 18,000 to 36,000 BTU … ducted units from 18,000 to 60,000 BTU and cassettes from 36,000 to 48,000 BTU … plus window and portable units"; "A UAE brand with wide after-sales reach" | Omar: text contradicts the imported catalogue (pending manual edit in the roadmap). | Unchanged. |
| 26 | Carrier: "from a 1-ton wall split to chilled-water plant … submittal documents consultants accept without discussion" | Omar: pending manual edit; unit wording. | Unchanged. |
| 27 | O General "in the Middle East market since 1971", "the brand most villa owners ask for by name"; Coolex "manufactured in Kuwait by RIC since 1986 … UL, AHRI and Eurovent certification" | Omar: source for each statement. | Unchanged. |

## Maintenance

| # | Text affected | To confirm | Placeholder meanwhile |
|---|---|---|---|
| 28 | "Two to four visits a year … with a report after each visit." | Ahmad: actual contract terms. | Kept. |
| 29 | "Original spare parts … for the seven brands" | Ahmad: parts for which brands. | "for the brands we supply". |
| 30 | "including removal and disposal of the old equipment" | Ahmad: confirm. | Kept. |

## Duct cleaning (new)

| # | Text affected | To confirm | Placeholder meanwhile |
|---|---|---|---|
| 31 | Whole page (`/duct-cleaning/`) | Ahmad: method and equipment used, what a visit includes, property types served, areas served, whether a report or photos are given, whether disinfection is offered. | Page published in Phase 3. It says only that the service exists and lists what the customer should tell us (type of property, system, location, access). No method, duration, price, guarantee or coverage is stated. |

## Contact (new)

| # | Text affected | To confirm | Placeholder meanwhile |
|---|---|---|---|
| 32 | Map / location | Ahmad: Google Maps link or coordinates; landline number if any. | Address text and mobile number only. |

## FAQ (new page)

| # | Text affected | To confirm | Placeholder meanwhile |
|---|---|---|---|
| 33 | Six existing questions | Ahmad: any questions to add (warranty, payment terms, service areas, duct cleaning). | Existing six, unchanged. |

## About (new page)

| # | Text affected | To confirm | Placeholder meanwhile |
|---|---|---|---|
| 34 | Company description (`/about/`) | Ahmad: year founded, team size, own installation team, notable project types that may be named. | Page published in Phase 3 with the existing About text from the home page and a list of the services; no history or figures. |

## Privacy Policy (new)

| # | Text affected | To confirm | Placeholder meanwhile |
|---|---|---|---|
| 35 | Retention | Ahmad / Omar: how long quote requests are kept. | "kept for as long as needed to handle the request" — no period stated. |
| 36 | Data controller contact | Ahmad: name or role and address for privacy requests. | info@opalgalaxy.ae. |
| 37 | Applicable law | Opal's legal adviser. | No law named. |
| 38 | "Requests are saved in the website's database, where the company's website administrators can read them, and they are passed to the company's sales team so that they can reply to you." | Omar: is `N8N_QUOTE_WEBHOOK` set on staging / at launch, where is n8n hosted, and what does it send onward (WhatsApp, email)? Are backups (S3) to be mentioned? Is "website administrators" the right description of Omar Digital's role? | As quoted; no tool or provider named. |
| 39 | Third parties | Omar: Cloudflare is in front of the site; Google Fonts is contacted until fonts are self-hosted. Mention them? | Cloudflare mentioned as the delivery network; Google Fonts removed by self-hosting. |
| 40 | Cookie | Omar: the site sets one security cookie (`csrftoken`) for the form. Wording approval. | Stated factually as a security cookie; no tracking cookies. |

## Arabic language notes (existing fields)

Status after Phase 3: L1–L6, L10–L16, L18, L20, L21, L23, L25 and L26 were applied by the guarded migration `core 0005` (a phrase is replaced only where the old phrase still stands). L7–L9 (units), L17, L19 and L22 remain open with their owners.

Every text below has its own Arabic field in the admin and can be edited there; none needs a code change. The only texts with no Arabic field are the catalogue rows (`Series / models` and `specs` of each brand row), covered by question 8c. Each note gives the admin location, the current text, and a suggested wording. Nothing here is changed by the redesign until Omar approves it.

| # | Admin location · field | Current Arabic text | Note | Suggested wording |
|---|---|---|---|---|
| L1 | Products → Ducted split · name (AR) | وحدات مخفية (Ducted) | English word inside the Arabic name. | وحدات مخفية |
| L2 | Products → Package / rooftop · name (AR) | وحدات مجمّعة (Package) | English word inside the Arabic name. | وحدات مجمّعة |
| L3 | Products → Chillers, AHU and fan coils · name (AR) | شيلرات ووحدات مناولة الهواء | The English name also has fan coils; "شيلرات" is a transliteration. Choose one term for the whole site. | مبرّدات المياه ووحدات مناولة الهواء ووحدات الملف والمروحة — or keep "شيلرات" everywhere and add "وفان كويل" |
| L4 | Products → Ducted split · lead (AR) | …تغذي فتحات التوزيع عبر مجاري الهواء، ووحدة خارجية لكل منطقة. | "مجاري الهواء" here, "مجاري التكييف" in the duct cleaning service. One term for ducts. | …عبر مجاري التكييف، مع وحدة خارجية لكل منطقة. |
| L5 | Products → Wall mounted split · lead (AR) | …دون مجارٍ للهواء. | Same term as L4. | …دون مجاري تكييف. |
| L6 | Products → Package / rooftop · lead and "Good to know" (AR) | يُوصَل بمجاري الهواء · تُوصل بمجاري الهواء والكهرباء فقط | Same term as L4. | بمجاري التكييف |
| L7 | Products → VRF systems · capacity range | 4 – 80 HP per system | English phrase on the Arabic page. The field has one value for both languages (unit audit, 8b). | 4 – 80 HP (and a separate Arabic range field, if wanted) |
| L8 | Products → Package / rooftop, Chillers · capacity range | 3 – 100 ton · 3 – 500 ton | "ton" on Arabic pages (unit audit, 8b). | Omar's decision |
| L9 | Pages → Home → Gallery photos · caption (AR) | O General 5 ton · Midea Package 15 ton · Midea 5 ton | English "ton" and "Package" in Arabic captions (unit audit, 8b; caption facts, question 20). | Omar's decision |
| L10 | Pages → Home → Gallery photos · caption (AR) | وحدتان Inverter | Latin term where Arabic exists. | وحدتان بتقنية Inverter — or وحدتان بضاغط متغيّر السرعة |
| L11 | Pages → Home → FAQ · answer (AR), T3 question | مختبرة عند حرارة خارجية 46° مئوية، بخلاف T1 المختبرة عند 35°. | Degree style differs from the product pages ("46 °م"). | مختبرة عند درجة حرارة خارجية تبلغ 46 °م، بخلاف T1 المختبرة عند 35 °م. |
| L12 | Pages → Home → FAQ · answer (AR), quote question | عبر النموذج أدناه أو بإرسال جدول الكميات (BOQ)… نرد خلال يوم عمل واحد. | "(BOQ)" in brackets; "نرد" is plain beside "سنوافيكم بالرد" used elsewhere. Also an unverified claim (question 11). | عبر النموذج أدناه، أو بإرسال جدول الكميات أو مخططات التكييف عبر واتساب، وسنوافيكم بالرد خلال يوم عمل واحد. |
| L13 | Pages → Home → FAQ · answer (AR), documents question | مستندات الاعتماد (Submittals) وكتالوجات المصنّع | English in brackets; "المصنّع" vs "الشركة المصنّعة" elsewhere. | مستندات الاعتماد وكتالوجات الشركة المصنّعة |
| L14 | Pages → Home → FAQ · answers (AR) | R22 غاز قديم يُبقى عليه… · يُذكر نوع الغاز | "غاز" alone vs "غاز التبريد" elsewhere. | غاز التبريد (throughout) |
| L15 | Pages → Home → About · text (AR) | تعمل الشركة حلقة وصل بين الوكلاء المعتمدين والمقاولين | Grammatically sound; reads more naturally with "بوصفها". | تعمل الشركة بوصفها حلقة وصل بين الوكلاء المعتمدين والمقاولين |
| L16 | Pages → Home → Contractors · lead (AR) | بصفة مورّد معتمد | "معتمد" suggests an official approval; the English says "standing supplier". | بصفة مورّد دائم |
| L17 | Pages → Home → Facts · text (AR) | في دبي والشارقة وعجمان، وإلى بقية الإمارات وفق حجم الطلب | No full stop, unlike the other texts. Unverified claim (question 10). | Add the full stop once the claim is confirmed. |
| L18 | Settings → Company details · footer_about (AR) | Opal Galaxy Air Condition Trading L.L.C — شركة توريد أنظمة تكييف… | Sentence opens with the Latin legal name and a dash. | شركة Opal Galaxy لتجارة مكيفات الهواء: توريد أنظمة التكييف للمقاولين والمشاريع والفلل في دولة الإمارات. |
| L19 | Settings → Company details · hours_full (AR) | السبت – الخميس، 8:00 – 18:00 · الأحد عطلة | Contradiction (question 1). | After Ahmad confirms. |
| L20 | Brands → Coolex · line (AR) | …وتبريد دقيق وVRF | Arabic "و" joined to a Latin word. Site-wide rule needed (also "وR410A", "وRotary", "وBMS"). | …وتبريد دقيق وأنظمة VRF — rule: put an Arabic noun before the Latin term |
| L21 | Brands → Coolex · about (AR) | Coolex هي الخيار خليجي الصنع | Missing definite article on the adjective. | Coolex هي الخيار الخليجي الصنع |
| L22 | Brands → Super General · about (AR) | بضواغط Inverter وRotary وReciprocating وScroll | Four Latin terms in a row; contradicts the imported data (question 25). | With the manual rewrite of this text. |
| L23 | Brands → Westpoint · about (AR) | أرضية-سقفية | Hyphen here, spaced dash in the category name "أرضية – سقفية". | أرضية – سقفية |
| L24 | Products → Chillers · lead and "Good to know" (AR) | فان كويل · شيلرات Screw وScroll | Transliteration and Latin terms; follows the decision in L3. | وحدات الملف والمروحة · مبرّدات لولبية وحلزونية — or keep the trade terms consistently |
| L25 | Pages → Maintenance · item text (AR) | للعلامات السبع | States a count (approved correction 1); fixed in Phase 3. | للعلامات التجارية التي نورّدها |
| L26 | Pages → Maintenance · item text (AR) | وفحص ضغط الغاز والكهرباء | "الغاز" as in L14. | وفحص ضغط غاز التبريد والتوصيلات الكهربائية |

Display notes from the visual consistency audit (content, for Omar in the admin; not changed by the redesign):

- Business hours on Arabic pages: "السبت – الخميس، 8:00 – 18:00 · الأحد عطلة" renders the time range as "18:00 – 8:00" because the digits and the dash sit inside right-to-left text. Writing it as "من 8:00 إلى 18:00" avoids the reversal. The contradiction itself is question 1.
- English footer description begins with the legal name and a dash ("Opal Galaxy Air Condition Trading L.L.C — air-conditioning supplier…"); the Arabic one was corrected in Phase 3.

Admin display note: Arabic fields in the admin are laid out left-to-right, so a full stop at the end of an Arabic sentence appears at the wrong end while editing. The public site shows it correctly. The fields can be given right-to-left direction in the admin in a later phase.

Terminology decisions (Omar, 23 Nov 2026) — applied to all new copy, and to the existing texts above in Phase 3 through a guarded migration:

1. Ducts: "مجاري التكييف" everywhere (L4, L5, L6).
2. Trade terms stay as the market uses them: "شيلرات", "فان كويل", "كاسيت" (L3: the Arabic category name becomes "شيلرات ووحدات مناولة الهواء وفان كويل"; L24 keeps "فان كويل").
3. Technical Latin terms (Inverter, Rotary, Scroll, VRF, BMS) stay in Latin, with an Arabic noun before them (L10, L20, L22, L24).
4. Temperatures: the number with "°م" only, without the words "درجة حرارة" or "مئوية" (L11). To confirm with Omar: this is how "بدون درجة حرارة" was understood; the alternative reading is to drop temperature figures from the Arabic texts altogether.

## Task 9 — Quotation form improvements (recorded during Task 17-C, not changed)

| # | Text affected | To confirm | Placeholder meanwhile |
|---|---|---|---|
| T9-1 | Shared form heading "Request a project quote" / "طلب عرض سعر لمشروعكم" on the Maintenance page | Omar: the heading speaks of a project, but this page's requests are for maintenance or a spare part. | Shared form left unchanged. |
| T9-2 | "Fill in the form or send your BOQ on WhatsApp." and the button "Send your BOQ on WhatsApp" on the Maintenance page | Omar: a BOQ does not apply to a maintenance or spare-part request. | Shared form left unchanged. |
| T9-3 | Header label "Media" / "الوسائط" | Omar: Arabic wording for the Media link ("الوسائط" used; "معرض الصور" is the alternative). | "الوسائط". |
| T9-4 | Shared form on the AC duct cleaning page | Omar: the page asks for the type of property and the ceiling access, but the form has no field for either; customers can only write them in Notes. | Shared form left unchanged; the WhatsApp message lists the four headings. |
| T9-5 | Shared form heading and BOQ wording on the AC duct cleaning page (same texts as T9-1 and T9-2) | Omar: "project quote" and "BOQ" do not fit a cleaning inquiry. | Shared form left unchanged. |

## About page (Task 17-E): statements shown as stored, not emphasised and not changed

| # | Text affected | To confirm | Placeholder meanwhile |
|---|---|---|---|
| A-1 | "is a licensed air-conditioning trading company in Dubai" | Omar: licence number and whether to publish it (see 4). The company details panel leaves the licence line out until confirmed. | Lead shown as stored; no licence in the panel. |
| A-2 | "built on years of supplying and installing HVAC" | Omar: founding year or years in business (see 18, 34). | Shown as stored. |
| A-3 | "between the authorised distributors and the contractor: distributor pricing with the speed of a small supplier" | Omar: true for every brand listed; commercial claim (see 13, 18). | Shown as stored. |
| A-4 | "the model on the quote is the model that arrives on site, on the agreed date, with a warranty card in your name" | Omar: the three promises (see 18). | Shown as stored, as ordinary text. |
| A-5 | "Supply with installation on request" | Omar: own installation team or subcontracted (see 17). | Shown as stored. |
| A-6 | Business hours | Omar: left out of the About panel while question 1 is open; still shown where they already were. | Not shown on the About page. |
| A-7 | Page description (meta) is the whole lead, over 300 characters | Omar: for the postponed SEO phase. | Unchanged. |

## Contact page (Task 17-F)

| # | Text affected | To confirm | Placeholder meanwhile |
|---|---|---|---|
| C-1 | Business hours "Saturday – Thursday, 8:00 – 18:00 · Sunday closed" | Omar: contradictory (see 1). Not shown on the Contact page until verified; the stored value is untouched and still appears on the home page and in the footer. | Hidden on Contact and About. |
| C-2 | Licence "Dubai Department of Economy and Tourism" | Omar: authority name only, no licence number (see 4). Not shown on the Contact page until verified; stored value untouched. | Hidden on Contact and About. |
| C-3 | Address "St152 – Port Saeed, Deira, Dubai – UAE" | Omar: no building or office number, no map link, shown in Latin script on the Arabic page (see 3, 32). | Shown as stored. |
| T9-6 | Shared form on the Contact page | Omar: the form section repeats the phone and the email directly under the contact cards, its heading says "project quote", its text mentions a BOQ, and every field is about an equipment order although the page is for general contact. | Shared form left unchanged. |

## FAQ page (Task 17-G): statements in the answers, shown as stored and not highlighted

| # | Text affected | To confirm | Placeholder meanwhile |
|---|---|---|---|
| F-1 | "within 48 hours in Dubai, Sharjah and Ajman, and to other emirates depending on order size" | Omar: delivery commitment (see 10). | Shown as stored. |
| F-2 | "We reply within one working day." | Omar: response time (see 11). | Shown as stored. |
| F-3 | "A detailed quote with model numbers, a tax invoice, submittals and manufacturer catalogues, and warranty cards in the client's or project's name." | Omar: documents actually provided (see 15). | Shown as stored. |
| F-4 | "For the UAE climate we supply T3-rated units or equivalent" | Omar: true for every unit supplied? | Shown as stored. |
| F-5 | "R32 is the newest generation: higher efficiency and lower environmental impact." | Omar: general technical statement; keep as worded? | Shown as stored. |
| F-6 | "Use the form below, or send your BOQ or HVAC drawings on WhatsApp." | Omar: tied to the form wording handled in Task 9. | Shown as stored. |
| F-7 | No FAQPage structured data on the page | Omar: deferred with the SEO phase. | None added. |

## Privacy Policy (Task 17-H)

The published policy is unchanged. A proposed shorter text in both languages, with every statement that needs confirmation marked, is in `review/privacy-policy-proposal.md`.

| # | Finding | To confirm | Placeholder meanwhile |
|---|---|---|---|
| P-1 | The live site loads Cloudflare Web Analytics (`static.cloudflareinsights.com`); it is not in the repository, so it is switched on in Cloudflare. The policy does not mention it. | Omar: intended? | Policy unchanged; nothing changed in Cloudflare. |
| P-2 | "passed to the company's sales team" is, in code, a copy of the request sent to an n8n webhook when one is configured. | Omar: is it configured, where is it hosted, where does it send the request next? | Policy unchanged. |
| P-3 | No retention period; nothing deletes old requests; daily backups hold copies. | Omar / company: retention wanted? | Policy unchanged. |
| P-4 | Server, backup storage and automation locations unknown. | Omar: countries, for any cross-border statement. | Policy unchanged. |
| P-5 | No date, no governing law, no contact beyond one email address. | Company's adviser. | Policy unchanged. |
| P-6 | The quote form is shown under the policy ("Show quote form" is ticked for this page). | Omar: untick in the admin if not wanted. | Left as set. |

## Task 20 — Launch readiness: intermittent 502 responses on staging (recorded 24 Nov 2026, Task 17-I)

Importance: high for launch. Cause not established; nothing was changed.

| Item | Detail |
|---|---|
| What happened | 6 of 270 page loads returned **502 Bad Gateway** during the Task 17-I crawl of https://new.opal-galaxy.com. |
| Affected requests | The page requests themselves: `/ar/duct-cleaning/` (1), `/ar/privacy/` (2), `/ar/gallery/` (2), `/ar/faq/` (1). All six were Arabic addresses; whether that is a coincidence is not known. |
| Viewports of the affected loads | 1024 px (three) and 390 px (three). The viewport is unlikely to matter; it only identifies which crawler was running. |
| Concurrency | Three headless Chromium crawlers at the same time, each loading 27 pages in two languages one after another (about three page loads in flight, each with its static files). |
| When retried | Each of the four addresses returned 200 three times in a row when fetched one at a time, minutes later. All 64 internal links returned 200 when checked sequentially. |
| Not observed | No 502 in any earlier single-browser check of the same pages on 23 and 24 Nov. |
| Not known | Whether the 502 came from Cloudflare, the Coolify proxy or the application; the number of Gunicorn workers on staging; whether a deploy or restart overlapped with the crawl; server load at the time. I have no access to server or proxy logs. |

Reproduction steps (read-only, no data is written):

1. From one machine, start three browsers (or three `curl` loops) against staging at the same time.
2. In each, request the 27 internal pages in English and Arabic in sequence, including their static files.
3. Count responses with status 502.
4. Compare with the same run using one browser only.

To look at when it is reproduced: the proxy and application logs for the timestamps of the 502s, the worker count and timeout of the application server, and container restarts during the run.

## Status updates backed by evidence (24 Nov 2026, Task 17-I)

Only items that the live site or the code now proves are marked. Everything else above stays open for Tasks 18 to 20.

| # | Item | Status | Evidence |
|---|---|---|---|
| 6 | Brand pages for SKM, LG, Daikin, Trane | Pages exist and are published; their texts are still Omar's to write | `/brands/skm/`, `/brands/lg/`, `/brands/daikin/`, `/brands/trane/` return 200 in both languages and show the "confirmed on the quote" state |
| 39 | Third parties: Google Fonts | Resolved for fonts | 264 live page loads contacted no host other than the site itself and `static.cloudflareinsights.com`; fonts are self-hosted. The Cloudflare Web Analytics part stays open as P-1 |
| P-6 | Quote form shown under the Privacy Policy | Resolved | `/privacy/` and `/ar/privacy/` no longer render the form (Omar unticked the option in the admin) |
| QA-01 | Breadcrumb alignment and leading Arabic separator | Resolved and confirmed on staging (24 Nov, after the deploy of `b6c6859`) | Before: items 4 to 5 px apart on desktop, 10 to 11 px on phones. After, on the live site: 11 page types in both languages at 5 widths (110 loads), items 0.0 px apart, one separator fewer than items, none before the first Arabic item |
| QA-03 | Heading level skipped in the technical panels (h2 then h4) | Fixed in this PR | Tests in `HeadingOrderTests`; computed style, size and position of the headings identical before and after |
| QA-04 | Page descriptions of brands without text (brand name only) and descriptions over 200 characters | Deferred to the SEO and launch QA work | `templates/catalog/brand.html` line 3 |
| QA-05 | Arabic lead line length at 1024 px on brand and category pages | Deferred; no layout change now (Omar, 24 Nov) | Crawl measurement |

