from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path, re_path
from django.views.static import serve
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from core import views

urlpatterns = [
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("quote/", views.quote_submit, name="quote_submit"),
    path("robots.txt", views.robots_txt),
    path("sitemap.xml", views.sitemap_xml),
    path("health", views.health),
    # Media is small (a few dozen product photos), so Django serves it directly.
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
urlpatterns += i18n_patterns(path("", include(wagtail_urls)), prefix_default_language=False)
