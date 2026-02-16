from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def listings_page(request):
    return render(request, "marketplace/listings.html")


@ensure_csrf_cookie
def listing_detail_page(request, listing_id):
    return render(request, "marketplace/detail.html", {"listing_id": listing_id})


@login_required
@ensure_csrf_cookie
def publish_listing_page(request):
    return render(request, "marketplace/publish.html")
