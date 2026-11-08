"""Bilingual helpers. Content models keep *_en / *_ar field pairs; English is the fallback."""
from django.utils.translation import get_language

LANGS = ("en", "ar")


def current_lang():
    lang = (get_language() or "en")[:2]
    return lang if lang in LANGS else "en"


def tr(obj, field, lang=None):
    lang = lang or current_lang()
    value = getattr(obj, f"{field}_{lang}", "") or ""
    if not value and lang != "en":
        value = getattr(obj, f"{field}_en", "") or ""
    return value


def lang_url(path, lang=None):
    """Prefix a site path for the given language. English has no prefix."""
    lang = lang or current_lang()
    path = path if path.startswith("/") else "/" + path
    return ("/ar" + path) if lang == "ar" else path


def strip_lang(path):
    if path == "/ar" or path.startswith("/ar/"):
        return path[3:] or "/"
    return path
