from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class CanonicalDomainRedirectMiddleware:
    LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEBUG or request.method not in ("GET", "HEAD"):
            return self.get_response(request)

        canonical = (getattr(settings, "CANONICAL_HOST", "") or "").strip().lower()
        if not canonical:
            return self.get_response(request)

        canonical = canonical.removeprefix("www.")

        forwarded_host = request.META.get("HTTP_X_FORWARDED_HOST", "")
        host_header = (forwarded_host or request.META.get("HTTP_HOST", "")).split(",")[0].strip()

        netloc = host_header
        if host_header.count(":") == 1 and not host_header.startswith("["):
            host, port_number = host_header.rsplit(":", 1)
            port = f":{port_number}"
        else:
            host = host_header
            port = ""

        host = host.strip("[]").lower()
        if host in self.LOCAL_HOSTS or host == canonical.lower():
            return self.get_response(request)

        if host != f"www.{canonical}":
            return self.get_response(request)

        url = request.build_absolute_uri(request.get_full_path())
        parts = urlsplit(url)

        new_url = urlunsplit((parts.scheme, canonical + port, parts.path, parts.query, parts.fragment))
        return HttpResponsePermanentRedirect(new_url)
