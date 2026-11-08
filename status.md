# Opal Galaxy (Wagtail) — status.md
**آخر تحديث: 8 نوفمبر 2026 · الإصدار: v0.1 (أول بناء ديناميكي)**

## المنجز
- مشروع Wagtail 7.0 LTS / Django 5.2 LTS ينقل المعاينة الثابتة v0.7 تصميماً ومحتوى.
- المحتوى مستخرج آلياً من `opal-static`: 7 ماركات، 10 أنواع منتجات، 36 خلية في المصفوفة، FAQ، المعرض، 18 صورة → `seed/opal.json`.
- روابط حقيقية لكل صفحة باللغتين (`/` إنجليزي، `/ar/` عربي) + hreflang + canonical + sitemap.xml.
- نموذج طلب السعر يعمل: يُحفظ في قاعدة البيانات (Admin → Quote requests) ويُرسل إلى n8n عبر `N8N_QUOTE_WEBHOOK`؛ honeypot ضد البوتات.
- `noindex` افتراضي حتى اعتماد أحمد (`SITE_NOINDEX=0` لاحقاً).
- إصلاحات مقارنة بالمعاينة الثابتة: زر اللغة كان مقصوصاً في هيدر الجوال؛ هامش "Other products".
- 10 اختبارات آلية تمر على PostgreSQL 16؛ تشغيل الحاوية مُحاكى بالكامل (migrate → seed → admin → gunicorn).

## قرارات
- PostgreSQL (لا SQLite).
- ريبو جديد منفصل + staging منفصل؛ المعاينة الثابتة تبقى حتى الاعتماد.
- المحتوى ثنائي اللغة بحقول `_en/_ar` جنباً إلى جنب في اللوحة (بدون wagtail-localize) لتبسيط الأتمتة.

## المتبقي
1. نسخة PostgreSQL على السيرفر (تُؤكَّد قبل الإنشاء).
2. Coolify: تطبيق جديد في مشروع opal + قاعدة PostgreSQL + volume `/app/data` + المتغيرات + دومين staging.
3. Cloudflare: سجل الـ staging.
4. أول Run workflow ثم فحص الموقع وتحويله proxied.
5. مراجعة أحمد للموقع على staging ← تحويل الدومين الرئيسي و `SITE_NOINDEX=0`.
6. صيغة الـ brief العامة (od-wagtail) مستخرجة من هذا المشروع.
