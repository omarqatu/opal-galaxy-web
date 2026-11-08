import logging
import threading
from urllib.parse import urlsplit

import requests
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.utils import timezone

from catalog.models import Brand, ProductCategory
from .models import QuoteRequest, ServicePage

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
    paths += [f"/products/{c.slug}/" for c in ProductCategory.objects.all()]
    paths += [f"/brands/{b.slug}/" for b in Brand.objects.all()]
    paths += [f"/{p.slug}/" for p in ServicePage.objects.live()]
    return render(request, "sitemap.xml", {"base": base, "paths": paths,
                                           "today": timezone.localdate()}, content_type="application/xml")


def health(request):
    return HttpResponse("ok", content_type="text/plain")
