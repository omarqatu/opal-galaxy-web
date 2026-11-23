# Open questions — Opal Galaxy website

Maintained through the redesign (last update: Phase 2, 23 Nov 2026). Catalogue questions stay in `review/questions.md`.

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
| 8c | Spec lines on Arabic pages (stored in English only) | Omar: keep them in English in a left-to-right technical block (recommended), translate recurring terms at display time, or add an Arabic field. Needed before Phase 3. | Shown in English, as today. |
| 8 | "We never share your details." / "لن تتم مشاركة بياناتكم مع أي جهة." | Omar: requests are forwarded to an n8n webhook when configured; confirm the sentence is still true, or reword. | Sentence kept, linked to the Privacy Policy. |

## Home

| # | Text affected | To confirm | Placeholder meanwhile |
|---|---|---|---|
| 8d | Hero and contractors photographs | Phase 2 uses two genuine gallery photos (two outdoor units beside a villa; crane lift). Both are small phone photos (675×900). Ahmad: new photographs as listed in the Phase 0 report. | Existing gallery photos in portrait frames. |
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
| 31 | Whole page | Ahmad: method and equipment used, what a visit includes, property types served, areas served, whether a report or photos are given, whether disinfection is offered. | General description of the service with no method, duration, price, guarantee or coverage stated. |

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
| 34 | Company description | Ahmad: year founded, team size, own installation team, notable project types that may be named. | Existing About text only; no history or figures. |

## Privacy Policy (new)

| # | Text affected | To confirm | Placeholder meanwhile |
|---|---|---|---|
| 35 | Retention | Ahmad / Omar: how long quote requests are kept. | "kept for as long as needed to handle the request" — no period stated. |
| 36 | Data controller contact | Ahmad: name or role and address for privacy requests. | info@opalgalaxy.ae. |
| 37 | Applicable law | Opal's legal adviser. | No law named. |
| 38 | Where submissions go | Omar: is `N8N_QUOTE_WEBHOOK` set on staging / at launch, where is n8n hosted, and what does it send onward (WhatsApp, email)? Are backups (S3) to be mentioned? | States only: saved in the website's database and visible to the company's site administrators. |
| 39 | Third parties | Omar: Cloudflare is in front of the site; Google Fonts is contacted until fonts are self-hosted. Mention them? | Cloudflare mentioned as the delivery network; Google Fonts removed by self-hosting. |
| 40 | Cookie | Omar: the site sets one security cookie (`csrftoken`) for the form. Wording approval. | Stated factually as a security cookie; no tracking cookies. |
