import json
import tempfile
from decimal import Decimal
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from catalog.models import Brand, ProductCategory, Supply


def row(**kw):
    base = {"category": "window", "models": "SGA25AE", "specs": ["R410A", "T3 rotary compressor"],
            "confirmed_on_quote": False, "source": "Super General Window AC sheet 2025, p.1",
            "source_type": "manufacturer_catalogue"}
    base.update(kw)
    return base


class ImportCatalogueTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def run_import(self, rows, apply=False, brand="super-general", **top):
        data = {"schema": 1, "brand": brand, "rows": rows, **top}
        f = self.tmp / "in.json"
        f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        out = StringIO()
        args = [str(f), "--review-dir", str(self.tmp)] + (["--apply"] if apply else [])
        call_command("import_catalogue", *args, stdout=out)
        return out.getvalue()

    def assertRejected(self, rows, *fragments, drafts_before=0, **kw):
        with self.assertRaises(CommandError) as cm:
            self.run_import(rows, **kw)
        msg = str(cm.exception)
        for frag in fragments:
            self.assertIn(frag, msg)
        self.assertFalse(Supply.objects.filter(models_text="SGA25AE").exists())
        self.assertEqual(ProductCategory.objects.filter(has_unpublished_changes=True).count(), drafts_before)
        return msg

    def sg_window(self):
        return Supply.objects.get(category__slug="window", brand__slug="super-general")

    # ---------------------------------------------------------------- dry run
    def test_dry_run_prints_diff_and_writes_nothing(self):
        before = self.sg_window().models_text
        out = self.run_import([row()])
        self.assertIn("[window]", out)
        self.assertIn(f"models: {before}  →  SGA25AE", out)
        self.assertIn("source_type: unknown  →  manufacturer_catalogue", out)
        self.assertIn("Dry run", out)
        self.assertEqual(self.sg_window().models_text, before)
        self.assertFalse(ProductCategory.objects.get(slug="window").has_unpublished_changes)
        review = (self.tmp / "super-general-review.md").read_text(encoding="utf-8")
        self.assertIn("| window | models |", review)
        self.assertIn("Super General Window AC sheet 2025, p.1", review)
        self.assertIn("Dry run", review)

    # ---------------------------------------------------------------- apply
    def test_apply_saves_draft_only_and_site_is_unchanged(self):
        before = self.sg_window().models_text
        self.run_import([row(nominal_tons_min="1.5", nominal_tons_max="2", tons_stated_in_source=True)], apply=True)
        cat = ProductCategory.objects.get(slug="window")
        self.assertTrue(cat.live)
        self.assertTrue(cat.has_unpublished_changes)
        self.assertEqual(self.sg_window().models_text, before)  # live row untouched
        r = self.client.get("/products/window/")
        self.assertContains(r, before)
        self.assertNotContains(r, "SGA25AE")
        # The draft holds the new values
        draft = cat.latest_revision.as_object()
        s = next(x for x in draft.supplies.all() if x.brand.slug == "super-general")
        self.assertEqual((s.models_text, s.specs, s.source_type), ("SGA25AE", "R410A\nT3 rotary compressor",
                                                                   "manufacturer_catalogue"))
        self.assertEqual((s.nominal_tons_min, s.nominal_tons_max), (Decimal("1.5"), Decimal("2")))
        # Other brands' rows in the same category are carried over unchanged
        self.assertEqual(len(draft.supplies.all()), cat.supplies.count())
        # Publishing (by Omar, in the admin) makes it public
        cat.latest_revision.publish()
        self.assertContains(self.client.get("/products/window/"), "SGA25AE")

    def test_apply_adds_new_row_in_existing_category_as_draft(self):
        self.assertFalse(Supply.objects.filter(category__slug="floor-standing", brand__slug="super-general").exists())
        out = self.run_import([row(category="floor-standing", models="SGFS36AE · SGFS48AE")], apply=True)
        self.assertIn("NEW ROW", out)
        self.assertFalse(Supply.objects.filter(category__slug="floor-standing", brand__slug="super-general").exists())
        self.assertNotContains(self.client.get("/brands/super-general/"), "SGFS36AE")
        cat = ProductCategory.objects.get(slug="floor-standing")
        cat.latest_revision.publish()
        self.assertTrue(Supply.objects.filter(category__slug="floor-standing", brand__slug="super-general",
                                              models_text="SGFS36AE · SGFS48AE").exists())

    def test_never_publishes_never_deletes(self):
        live_rows = Supply.objects.count()
        self.run_import([row()], apply=True)
        self.assertEqual(Supply.objects.count(), live_rows)
        cat = ProductCategory.objects.get(slug="window")
        self.assertNotEqual(cat.live_revision_id, cat.latest_revision_id)

    def test_existing_draft_is_never_overwritten(self):
        cat = ProductCategory.objects.get(slug="window")
        cat.lead_en = "Someone's manual draft"
        cat.save_revision()
        rev = cat.latest_revision_id
        self.assertRejected([row()], "already has an unpublished draft", drafts_before=1)
        cat.refresh_from_db()
        self.assertEqual(cat.latest_revision_id, rev)

    def test_unchanged_row_writes_no_revision(self):
        s = self.sg_window()
        s.specs, s.source = "R410A\nT3 rotary compressor", "X"
        s.save()
        r = row(models=s.models_text, source="X", source_type="unknown")
        out = self.run_import([r], apply=True)
        self.assertIn("[window] no change", out)
        self.assertFalse(ProductCategory.objects.get(slug="window").has_unpublished_changes)

    def test_hold_rows_are_skipped_and_listed(self):
        out = self.run_import([row(), row(category="cassette", models="42MEL hold me", hold=True,
                                          note="awaiting client")], apply=True)
        self.assertIn("[cassette] HOLD, skipped: 42MEL hold me", out)
        self.assertFalse(ProductCategory.objects.get(slug="cassette").has_unpublished_changes)
        review = (self.tmp / "super-general-review.md").read_text(encoding="utf-8")
        self.assertIn("On hold", review)
        self.assertIn("42MEL hold me", review)

    def test_rows_not_in_file_are_listed_untouched(self):
        out = self.run_import([row()])
        self.assertIn("[wall] not in the file, left untouched", out)

    def test_review_lists_manual_edits(self):
        self.run_import([row()])
        review = (self.tmp / "super-general-review.md").read_text(encoding="utf-8")
        self.assertIn("## تعديل يدوي مطلوب", review)
        self.assertIn("about text (EN)", review)
        self.assertIn("Wall splits from 18,000", review)
        self.assertIn("Category “window” capacity range: 18,000 – 27,000 BTU", review)

    # ---------------------------------------------------------------- rejection
    def test_unknown_brand_and_category(self):
        self.assertRejected([row(category="spaceship")], "unknown category slug 'spaceship'", brand="nope")
        self.assertRejected([row()], "Unknown brand slug 'nope'", brand="nope")
        self.assertEqual(Brand.objects.count(), 11)
        self.assertEqual(ProductCategory.objects.count(), 10)

    def test_models_and_source_required(self):
        self.assertRejected([row(models=" ", source="")], "models (series / models) is required",
                            "source is required")

    def test_source_type_must_be_valid(self):
        self.assertRejected([row(source_type="whatsapp")], "source_type must be one of")

    def test_spec_limits(self):
        self.assertRejected([row(specs=[f"line {i}" for i in range(13)])], "13 spec lines (max 12)")
        self.assertRejected([row(specs=["x" * 81])], "has 81 characters (max 80)")
        self.run_import([row(specs=["x" * 80] * 12)])  # exactly at the limits is fine

    def test_prices_rejected(self):
        for text in ["AED 1,499", "Price on request", "السعر 1500 درهم", "Dhs 900", "$499", "سعر خاص"]:
            with self.subTest(text=text):
                self.assertRejected([row(specs=[text])], "price or currency")

    def test_60hz_rejected(self):
        for text in ["220V/1Ph/60Hz", "60 Hz model", "50/60Hz"]:
            with self.subTest(text=text):
                self.assertRejected([row(specs=[text])], "60 Hz data is not allowed")
        self.assertRejected([row(source="CLK catalogue 60 Hz Oct 2020")], "60 Hz")
        self.run_import([row(specs=["220-240V/1Ph/50Hz", "60,000 BTU"])])  # 50 Hz and 60,000 are fine

    def test_tons_require_document_statement(self):
        self.assertRejected([row(nominal_tons_min="1.5")], "tons_stated_in_source is not true")
        self.assertRejected([row(specs=["18,000 BTU (1.5 ton)"])], "tons_stated_in_source is not true")
        self.assertRejected([row(specs=["5 TR"])], "tons_stated_in_source is not true")
        self.assertRejected([row(specs=["2 طن"])], "tons_stated_in_source is not true")
        self.run_import([row(specs=["1.5 Ton"], tons_stated_in_source=True)])

    def test_tons_must_be_exact_strings(self):
        self.assertRejected([row(nominal_tons_min=1.5, tons_stated_in_source=True)], "must be a string")
        self.assertRejected([row(nominal_tons_min="1.555", tons_stated_in_source=True)], "more than 2 decimals")
        self.assertRejected([row(nominal_tons_min="3", nominal_tons_max="2", tons_stated_in_source=True)],
                            "nominal_tons_min is larger")

    def test_empty_specs_need_confirmed_on_quote(self):
        self.assertRejected([row(specs=[])], "confirmed_on_quote must be true")
        self.run_import([row(specs=[], confirmed_on_quote=True)])

    def test_whole_file_rejected_and_all_errors_listed(self):
        msg = self.assertRejected(
            [row(), row(category="wall", specs=["AED 100"]), row(category="cassette", source="")],
            "price or currency", "source is required", "2 error(s)")
        self.assertIn("nothing imported", msg)

    def test_duplicate_category_and_unknown_keys(self):
        self.assertRejected([row(), row(colour="red")], "appears more than once", "unknown key 'colour'")
        self.assertRejected([row()], "Unknown top-level key 'extra'", extra=1)

    def test_bad_json(self):
        f = self.tmp / "bad.json"
        f.write_text("{nope", encoding="utf-8")
        with self.assertRaises(CommandError):
            call_command("import_catalogue", str(f), "--review-dir", str(self.tmp), stdout=StringIO())
