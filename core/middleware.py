from django.conf import settings


class RobotsHeaderMiddleware:
    """Keep preview deployments out of search engines (SITE_NOINDEX=1)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if settings.SITE_NOINDEX:
            response["X-Robots-Tag"] = "noindex, nofollow"
        return response
