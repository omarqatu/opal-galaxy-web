# Opal Galaxy (Wagtail) — status.md
**آخر تحديث: 17 نوفمبر 2026 · الإصدار: v0.2 (تجهيز استيراد المنتجات)**

## المنجز
- مشروع Wagtail 7.0 LTS / Django 5.2 LTS ينقل المعاينة الثابتة v0.7 تصميماً ومحتوى.
- المحتوى مستخرج آلياً من `opal-static`: 7 ماركات، 10 أنواع منتجات، 36 خلية في المصفوفة، FAQ، المعرض، 18 صورة → `seed/opal.json`.
- روابط حقيقية لكل صفحة باللغتين (`/` إنجليزي، `/ar/` عربي) + hreflang + canonical + sitemap.xml.
- نموذج طلب السعر يعمل: يُحفظ في قاعدة البيانات (Admin → Quote requests) ويُرسل إلى n8n عبر `N8N_QUOTE_WEBHOOK`؛ honeypot ضد البوتات.
- `noindex` افتراضي حتى اعتماد أحمد (`SITE_NOINDEX=0` لاحقاً).
- إصلاحات مقارنة بالمعاينة الثابتة: زر اللغة كان مقصوصاً في هيدر الجوال؛ هامش "Other products".
- 13 اختباراً آلياً تمر على PostgreSQL 17 (في الجلسة وفي CI)؛ تشغيل الحاوية مُحاكى بالكامل (migrate → seed → admin → gunicorn).

- لوحة التحكم: قائمتا **Products** و**Brands** في القائمة الرئيسية (بدل Snippets)، مع الاسم بالإنجليزية والعربية لأنواع المنتجات، والمنشأ باللغتين للماركات.
- `CLAUDE.md`: قواعد جلسات Claude Code؛ الاختبارات على PostgreSQL 17 عبر Docker.
- `notes.md`: سجل ملاحظات العميل (فارغ).

- المنشأ محذوف من الماركات بقرار العميل.
- أنواع المنتجات بمسودات ونسخ ومعاينة؛ الموقع العام يعرض المنشور فقط.
- صفوف الماركات فيها الأطنان الاسمية والمصدر ونوع المصدر.
- أمر `import_catalogue` (تجربة افتراضياً، `--apply` = مسودات فقط، وملف مراجعة للعميل).
- جرد الكتالوجات `data/inventory.csv`، وملف Super General `data/super-general.json`، والأسئلة المفتوحة `review/questions.md`.

## قرارات
- PostgreSQL 17 (لا SQLite)، في الإنتاج والاختبارات.
- ريبو جديد منفصل + staging منفصل؛ المعاينة الثابتة تبقى حتى الاعتماد.
- المحتوى ثنائي اللغة بحقول `_en/_ar` جنباً إلى جنب في اللوحة (بدون wagtail-localize) لتبسيط الأتمتة.

## المتبقي
- تجربة `import_catalogue` (dry run) على `data/super-general.json` في جلسة سحابية، ثم مراجعة العميل لـ `review/super-general-review.md` و`review/questions.md`.
1. Coolify: تطبيق جديد في مشروع opal + قاعدة PostgreSQL + volume `/app/data` + المتغيرات + دومين staging.
2. Cloudflare: سجل الـ staging.
3. أول Run workflow ثم فحص الموقع وتحويله proxied.
4. مراجعة أحمد للموقع على staging ← تحويل الدومين الرئيسي و `SITE_NOINDEX=0`.
5. صيغة الـ brief العامة (od-wagtail) مستخرجة من هذا المشروع.
