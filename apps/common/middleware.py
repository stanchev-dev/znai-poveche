from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class CanonicalDomainRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        canonical = (getattr(settings, "CANONICAL_HOST", "") or "").strip()
        if canonical and request.method in ("GET", "HEAD"):
            host = request.get_host().split(":")[0].lower()
            if host != canonical.lower():
                url = request.build_absolute_uri(request.get_full_path())
                parts = urlsplit(url)

                # запази порт ако го има (рядко в production)
                netloc = parts.netloc
                port = ""
                if netloc.count(":") == 1:
                    port = ":" + netloc.split(":")[1]

                new_url = urlunsplit((parts.scheme, canonical + port, parts.path, parts.query, parts.fragment))
                return HttpResponsePermanentRedirect(new_url)

        return self.get_response(request)