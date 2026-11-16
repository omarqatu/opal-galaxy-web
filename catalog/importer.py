"""Catalogue import: validate a brand's JSON file, diff it against the site, write drafts.

The file format (schema 1):

    {"schema": 1, "brand": "<brand slug>", "rows": [{
        "category": "<category slug>",          # required
        "models": "...",                         # required, copied exactly
        "specs": ["...", ...],                   # max 12 lines, 80 chars each
        "confirmed_on_quote": false,             # must be true when specs is empty
        "nominal_tons_min": "1.5",               # strings, never numbers; optional
        "nominal_tons_max": "2",
        "tons_stated_in_source": true,           # required whenever tons appear
        "source": "Super General Window AC 2025, p.3",   # required
        "source_type": "manufacturer_catalogue", # see SOURCE_TYPES
        "note": "...",                           # optional, never published
        "hold": false                            # true: skipped and listed
    }]}

Nothing is ever published, deleted or created except draft revisions of existing
product categories (a new brand row inside an existing category is allowed).
"""
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.db import transaction

from .models import SOURCE_TYPES, Brand, ProductCategory, Supply

SCHEMA = 1
MAX_SPEC_LINES = 12
MAX_SPEC_CHARS = 80
SOURCE_MAX = Supply._meta.get_field("source").max_length
ROW_KEYS = {"category", "models", "specs", "confirmed_on_quote", "nominal_tons_min", "nominal_tons_max",
            "tons_stated_in_source", "source", "source_type", "note", "hold"}
TOP_KEYS = {"schema", "brand", "rows"}
SOURCE_TYPE_VALUES = {v for v, _ in SOURCE_TYPES}

PRICE_RE = re.compile(
    r"\bAED\b|\bDhs?\b|\bUSD\b|\bEUR\b|\bSAR\b|\bprices?\b|\bpriced\b|[$€£]"
    r"|درهم|دراهم|د\.إ|ريال|دولار|سعر|أسعار|اسعار|الأسعار|ثمن",
    re.IGNORECASE)
HZ60_RE = re.compile(r"60\s*-?\s*hz", re.IGNORECASE)
_AR = "\u0621-\u064a"
TONS_RE = re.compile(rf"(?i:\btons?\b)|\bTR\b|(?<![{_AR}])(?:طن|أطنان)(?![{_AR}])")

# Fields compared and written, in display order: (model field, label)
FIELDS = [("models_text", "models"), ("specs", "specs"), ("pending", "confirmed_on_quote"),
          ("nominal_tons_min", "nominal_tons_min"), ("nominal_tons_max", "nominal_tons_max"),
          ("source", "source"), ("source_type", "source_type")]


class ImportFileError(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("\n".join(errors))


@dataclass
class Change:
    category: str
    field: str
    old: str
    new: str
    source: str


@dataclass
class Plan:
    brand: Brand
    path: Path
    rows: list = field(default_factory=list)        # (category, values dict) to write
    changes: list = field(default_factory=list)     # Change
    new_rows: list = field(default_factory=list)    # category slugs that get a new row
    unchanged: list = field(default_factory=list)   # category slugs with no difference
    held: list = field(default_factory=list)        # (category slug, models, note)
    untouched: list = field(default_factory=list)   # this brand's rows not in the file
    manual: list = field(default_factory=list)      # (what, current value) to check by hand

    @property
    def changed_categories(self):
        seen = []
        for c in [ch.category for ch in self.changes] + self.new_rows:
            if c not in seen:
                seen.append(c)
        return seen


# ------------------------------------------------------------------ validation
def _decimal(value, label, where, errors):
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        errors.append(f"{where}: {label} must be a string copied from the document (e.g. \"1.5\"), not {value!r}")
        return None
    try:
        d = Decimal(value.strip())
    except InvalidOperation:
        errors.append(f"{where}: {label} {value!r} is not a number")
        return None
    if not d.is_finite() or d <= 0:
        errors.append(f"{where}: {label} {value!r} must be a positive number")
        return None
    if -d.as_tuple().exponent > 2 or d >= Decimal("10000"):
        errors.append(f"{where}: {label} {value!r} has more than 2 decimals or is too large")
        return None
    return d


def _strings(row):
    out = [row.get("models"), row.get("source"), row.get("note")]
    specs = row.get("specs")
    if isinstance(specs, list):
        out += specs
    return [s for s in out if isinstance(s, str)]


def validate(data):
    """Return (brand, cleaned rows, held rows) or raise ImportFileError listing every problem."""
    errors = []
    if not isinstance(data, dict):
        raise ImportFileError(["The file must contain a JSON object"])
    for k in sorted(set(data) - TOP_KEYS):
        errors.append(f"Unknown top-level key {k!r}")
    if data.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    brand = Brand.objects.filter(slug=data.get("brand") or "").first()
    if brand is None:
        errors.append(f"Unknown brand slug {data.get('brand')!r} (the importer never creates brands)")
    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        errors.append("rows must be a non-empty list")
        rows = []

    categories = {c.slug: c for c in ProductCategory.objects.all()}
    cleaned, held, seen = [], [], set()
    for i, row in enumerate(rows, 1):
        where = f"row {i}"
        if not isinstance(row, dict):
            errors.append(f"{where}: must be an object")
            continue
        slug = row.get("category")
        where = f"row {i} ({slug})"
        for k in sorted(set(row) - ROW_KEYS):
            errors.append(f"{where}: unknown key {k!r}")
        hold = row.get("hold", False)
        if not isinstance(hold, bool):
            errors.append(f"{where}: hold must be true or false")
        cat = categories.get(slug) if isinstance(slug, str) else None
        if cat is None:
            errors.append(f"{where}: unknown category slug {slug!r} (the importer never creates categories)")

        models_text = row.get("models")
        if not isinstance(models_text, str) or not models_text.strip():
            errors.append(f"{where}: models (series / models) is required")
        source = row.get("source")
        if not isinstance(source, str) or not source.strip():
            errors.append(f"{where}: source is required")
        elif len(source) > SOURCE_MAX:
            errors.append(f"{where}: source is longer than {SOURCE_MAX} characters")
        source_type = row.get("source_type")
        if source_type not in SOURCE_TYPE_VALUES:
            errors.append(f"{where}: source_type must be one of {', '.join(sorted(SOURCE_TYPE_VALUES))}")
        if "note" in row and not isinstance(row["note"], str):
            errors.append(f"{where}: note must be text")

        specs = row.get("specs", [])
        if not isinstance(specs, list) or not all(isinstance(s, str) for s in specs):
            errors.append(f"{where}: specs must be a list of text lines")
            specs = []
        specs = [s.strip() for s in specs]
        if any(not s for s in specs):
            errors.append(f"{where}: specs contains an empty line")
        if len(specs) > MAX_SPEC_LINES:
            errors.append(f"{where}: {len(specs)} spec lines (max {MAX_SPEC_LINES})")
        for n, s in enumerate(specs, 1):
            if len(s) > MAX_SPEC_CHARS:
                errors.append(f"{where}: spec line {n} has {len(s)} characters (max {MAX_SPEC_CHARS}): {s!r}")
            if "\n" in s:
                errors.append(f"{where}: spec line {n} contains a line break")
        confirmed = row.get("confirmed_on_quote", False)
        if not isinstance(confirmed, bool):
            errors.append(f"{where}: confirmed_on_quote must be true or false")
        elif not specs and not confirmed:
            errors.append(f"{where}: specs are empty, so confirmed_on_quote must be true")

        for text in _strings(row):
            m = PRICE_RE.search(text)
            if m:
                errors.append(f"{where}: price or currency ({m.group(0)!r}) is not allowed: {text!r}")
            if HZ60_RE.search(text):
                errors.append(f"{where}: 60 Hz data is not allowed: {text!r}")

        tmin = _decimal(row.get("nominal_tons_min"), "nominal_tons_min", where, errors)
        tmax = _decimal(row.get("nominal_tons_max"), "nominal_tons_max", where, errors)
        if tmin is not None and tmax is not None and tmin > tmax:
            errors.append(f"{where}: nominal_tons_min is larger than nominal_tons_max")
        stated = row.get("tons_stated_in_source", False)
        if not isinstance(stated, bool):
            errors.append(f"{where}: tons_stated_in_source must be true or false")
        published = [s for s in [models_text] + specs if isinstance(s, str)]
        has_tons = tmin is not None or tmax is not None or any(TONS_RE.search(s) for s in published)
        if has_tons and stated is not True:
            errors.append(f"{where}: tons appear but tons_stated_in_source is not true "
                          "(tons only where the document itself states them; never converted)")

        values = {
            "models_text": models_text.strip() if isinstance(models_text, str) else "",
            "specs": "\n".join(specs),
            "pending": confirmed is True,
            "nominal_tons_min": tmin, "nominal_tons_max": tmax,
            "source": source.strip() if isinstance(source, str) else "",
            "source_type": source_type,
        }
        if hold is True:
            held.append((slug, values["models_text"], row.get("note", "")))
            continue
        if slug in seen:
            errors.append(f"{where}: category {slug!r} appears more than once")
        seen.add(slug)
        if cat is not None:
            if cat.has_unpublished_changes:
                errors.append(f"{where}: category {slug!r} already has an unpublished draft. "
                              "Publish or discard it in the admin first; the importer never overwrites a draft")
            cleaned.append((cat, values))

    if errors:
        raise ImportFileError(errors)
    return brand, cleaned, held


# ------------------------------------------------------------------ planning
def _show(field_name, value):
    if value is None or value == "":
        return "—"
    if field_name == "pending":
        return "true" if value else "false"
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    return " / ".join(value.splitlines()) if field_name == "specs" else str(value)


def _differs(field_name, old, new):
    if field_name in ("nominal_tons_min", "nominal_tons_max"):
        return (old is None) != (new is None) or (old is not None and Decimal(old) != new)
    return old != new


def build_plan(path):
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ImportFileError([f"Cannot read {path}: {exc}"])
    brand, rows, held = validate(data)
    plan = Plan(brand=brand, path=path, rows=rows, held=held)
    in_file = {cat.slug for cat, _ in rows}
    for cat, values in rows:
        current = cat.supplies.filter(brand=brand).first()
        if current is None:
            plan.new_rows.append(cat.slug)
            for f, label in FIELDS:
                if values[f] not in (None, "", False) or f == "source_type":
                    plan.changes.append(Change(cat.slug, label, "(no row)", _show(f, values[f]), values["source"]))
            continue
        diffs = [Change(cat.slug, label, _show(f, getattr(current, f)), _show(f, values[f]), values["source"])
                 for f, label in FIELDS if _differs(f, getattr(current, f), values[f])]
        plan.changes += diffs
        if not diffs:
            plan.unchanged.append(cat.slug)
    for s in brand.supplies.select_related("category").order_by("category__sort_order"):
        if s.category.slug not in in_file and s.category.slug not in [h[0] for h in held]:
            plan.untouched.append((s.category.slug, s.models_text))
    if plan.changed_categories:
        plan.manual.append((f"Brand “{brand.name}” about text (EN)", brand.about_en))
        plan.manual.append((f"Brand “{brand.name}” about text (AR)", brand.about_ar))
        cats = {c.slug: c for c, _ in rows}
        for slug in plan.changed_categories:
            plan.manual.append((f"Category “{slug}” capacity range", cats[slug].capacity_range))
    return plan


# ------------------------------------------------------------------ applying
@transaction.atomic
def apply_plan(plan, user=None):
    """Save one draft revision per changed category. Never publishes."""
    revisions = []
    changed = set(plan.changed_categories)
    for cat, values in plan.rows:
        if cat.slug not in changed:
            continue
        cat = ProductCategory.objects.select_for_update().get(pk=cat.pk)
        if cat.has_unpublished_changes:
            raise ImportFileError([f"Category {cat.slug!r} got an unpublished draft during the import"])
        rows = list(cat.supplies.all())
        row = next((r for r in rows if r.brand_id == plan.brand.pk), None)
        if row is None:
            row = Supply(brand=plan.brand, sort_order=max([r.sort_order or 0 for r in rows], default=-1) + 1)
            rows.append(row)
        for f, _ in FIELDS:
            setattr(row, f, values[f])
        cat.supplies = rows
        revisions.append(cat.save_revision(user=user, log_action=True))
    return revisions


# ------------------------------------------------------------------ reporting
def _cell(text):
    return (text or "").replace("|", "\\|").replace("\n", " / ")


def diff_lines(plan):
    out = [f"Brand: {plan.brand.name} ({plan.brand.slug}) · file: {plan.path}"]
    for slug in plan.changed_categories:
        out.append(f"\n[{slug}]" + (" NEW ROW" if slug in plan.new_rows else ""))
        for ch in plan.changes:
            if ch.category == slug:
                out.append(f"  {ch.field}: {ch.old}  →  {ch.new}")
    for slug in plan.unchanged:
        out.append(f"\n[{slug}] no change")
    for slug, models_text, note in plan.held:
        out.append(f"\n[{slug}] HOLD, skipped: {models_text}" + (f" ({note})" if note else ""))
    for slug, models_text in plan.untouched:
        out.append(f"\n[{slug}] not in the file, left untouched: {models_text}")
    return out


def review_markdown(plan, applied):
    when = datetime.now().strftime("%Y-%m-%d %H:%M")
    mode = "Applied as unpublished drafts" if applied else "Dry run (nothing written to the site)"
    md = [f"# {plan.brand.name}: catalogue review", "",
          f"- File: `{plan.path.name}`", f"- Run: {when} · {mode}",
          "- Every line below is a value on the site that differs from the manufacturer's document. "
          "The document wins; please confirm each line.", "",
          "## Changes", ""]
    if plan.changes:
        md += ["| Category | Field | Current site value | New value (from the document) | Source |",
               "|---|---|---|---|---|"]
        md += [f"| {_cell(c.category)} | {c.field} | {_cell(c.old)} | {_cell(c.new)} | {_cell(c.source)} |"
               for c in plan.changes]
    else:
        md.append("No differences.")
    if plan.held:
        md += ["", "## On hold (not imported)", ""]
        md += [f"- {_cell(s)}: {_cell(m)}" + (f" ({_cell(n)})" if n else "") for s, m, n in plan.held]
    if plan.untouched:
        md += ["", "## Rows on the site not covered by this file (left untouched)", ""]
        md += [f"- {_cell(s)}: {_cell(m)}" for s, m in plan.untouched]
    if plan.manual:
        md += ["", "## تعديل يدوي مطلوب (manual edit required)", "",
               "The importer does not change these texts. Check each one against the new data above "
               "and edit it by hand in the admin if needed.", ""]
        md += [f"- {what}: {_cell(value) or '—'}" for what, value in plan.manual]
    return "\n".join(md) + "\n"
