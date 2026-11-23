import logging
import threading
from urllib.parse import urlsplit

import requests
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseNotAllowed, HttpResponseServerError
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone, translation

from catalog.models import Brand, ProductCategory
from .models import HomePage, QuoteRequest

log = logging.getLogger(__name__)


def _forward(qr_id):
    qr = QuoteRequest.objects.get(pk=qr_id)
    payload = {
        "id": qr.pk, "created": qr.created.isoformat(), "name": qr.name, "phone": qr.phone,
        "customer_type": qr.customer_type, "product": qr.product, "brand": qr.brand,
        "quantity": qr.quantity, "emirate": qr.emirate, "installation": qr.installation,
        "notes": qr.notes, "language": qr.language, "source_page": qr.source_page, "site": "opal-galaxy",
    }
    try:
        r = requests.post(settings.N8N_QUOTE_WEBHOOK, json=payload, timeout=10)
        r.raise_for_status()
        QuoteRequest.objects.filter(pk=qr.pk).update(forwarded=True)
    except Exception:  # noqa: BLE001 — the request is already saved; forwarding is best effort
        log.exception("Quote %s: n8n forward failed", qr.pk)


def _safe_back(request):
    ref = request.POST.get("source_page") or "/"
    parts = urlsplit(ref)
    path = parts.path if parts.path.startswith("/") and not parts.netloc else "/"
    return path


def quote_submit(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    back = _safe_back(request)
    p = request.POST
    if p.get("website"):  # honeypot: bots fill every field
        return redirect(f"{back}?sent=1#contact")
    phone = (p.get("phone") or "").strip()[:40]
    if len("".join(ch for ch in phone if ch.isdigit())) < 7:
        return redirect(f"{back}?sent=0#contact")
    try:
        qty = int(p.get("qty") or 0) or None
    except ValueError:
        qty = None
    qr = QuoteRequest.objects.create(
        name=(p.get("name") or "").strip()[:120], phone=phone,
        customer_type=(p.get("type") or "")[:20], product=(p.get("unit") or "")[:120],
        brand=(p.get("brand") or "")[:80], quantity=qty, emirate=(p.get("emirate") or "")[:40],
        installation=p.get("install") == "yes", notes=(p.get("notes") or "").strip()[:4000],
        language="ar" if p.get("lang") == "ar" else "en", source_page=back[:200],
    )
    if settings.N8N_QUOTE_WEBHOOK:
        threading.Thread(target=_forward, args=(qr.pk,), daemon=True).start()
    return redirect(f"{back}?sent=1#contact")


def robots_txt(request):
    if settings.SITE_NOINDEX:
        body = "User-agent: *\nDisallow: /\n"
    else:
        base = settings.SITE_BASE_URL or request.build_absolute_uri("/").rstrip("/")
        body = f"User-agent: *\nDisallow: /admin/\nSitemap: {base}/sitemap.xml\n"
    return HttpResponse(body, content_type="text/plain")


def sitemap_xml(request):
    base = settings.SITE_BASE_URL or request.build_absolute_uri("/").rstrip("/")
    paths = ["/"]
    paths += [f"/products/{c.slug}/" for c in ProductCategory.objects.live()]
    paths += [f"/brands/{b.slug}/" for b in Brand.objects.all()]
    home = HomePage.objects.live().first()
    if home:  # every published page under the home page: services, about, FAQ, contact, privacy…
        paths += [f"/{p.slug}/" for p in home.get_children().live().order_by("path")]
    return render(request, "sitemap.xml", {"base": base, "paths": paths,
                                           "today": timezone.localdate()}, content_type="application/xml")


def health(request):
    return HttpResponse("ok", content_type="text/plain")


def server_error(request):
    """Branded 500 page in the visitor's language. It uses no database, no context
    processors and no static files, so it still renders when one of those is the fault."""
    lang = "ar" if request.path == "/ar" or request.path.startswith("/ar/") else "en"
    try:
        with translation.override(lang):
            html = render_to_string("500.html", {"lang": lang, "dir": "rtl" if lang == "ar" else "ltr",
                                                 "home_url": "/ar/" if lang == "ar" else "/"})
    except Exception:  # noqa: BLE001 — never let the error page itself fail
        log.exception("500 page failed to render")
        html = "<!doctype html><title>Error</title><h1>Server error</h1>"
    return HttpResponseServerError(html)


def styleguide(request):
    """Design system reference, for review on staging only (never on an indexed site)."""
    if not settings.SITE_NOINDEX:
        raise Http404
    return render(request, "styleguide.html", {"page_kind": "styleguide"})
