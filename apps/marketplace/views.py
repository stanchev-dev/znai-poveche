from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import ListingEditForm
from .models import Listing


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


@login_required
def my_listings_page(request):
    listings = (
        Listing.objects.filter(owner=request.user)
        .select_related("subject")
        .order_by("-created_at")
    )
    return render(request, "marketplace/my_listings.html", {"listings": listings})


@login_required
def edit_listing_page(request, listing_id):
    listing = get_object_or_404(Listing.objects.select_related("owner"), pk=listing_id)
    if listing.owner_id != request.user.id:
        return HttpResponseForbidden("Нямаш достъп да редактираш тази обява.")

    if request.method == "POST":
        form = ListingEditForm(request.POST, instance=listing)
        if form.is_valid():
            form.save()
            messages.success(request, "Обявата е редактирана успешно.")
            return redirect("marketplace-my-listings-page")
    else:
        form = ListingEditForm(instance=listing)

    return render(request, "marketplace/edit_listing.html", {"form": form, "listing": listing})


@login_required
def delete_listing_page(request, listing_id):
    listing = get_object_or_404(Listing.objects.select_related("owner", "subject"), pk=listing_id)
    if listing.owner_id != request.user.id:
        return HttpResponseForbidden("Нямаш достъп да изтриеш тази обява.")

    if request.method == "POST":
        listing.delete()
        messages.success(request, "Обявата беше изтрита.")
        return redirect("marketplace-my-listings-page")

    return render(request, "marketplace/delete_listing_confirm.html", {"listing": listing})
