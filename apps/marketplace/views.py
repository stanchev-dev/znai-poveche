import json

from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import ListingEditForm, ListingImagesEditForm
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
    return render(
        request,
        "marketplace/publish.html",
        {"lesson_mode_choices": Listing.LessonMode.choices},
    )


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
    listing = get_object_or_404(Listing.objects.select_related("owner").prefetch_related("images"), pk=listing_id)
    if listing.owner_id != request.user.id:
        return HttpResponseForbidden("Нямаш достъп да редактираш тази обява.")

    image_form = ListingImagesEditForm(listing=listing)

    if request.method == "POST":
        form = ListingEditForm(request.POST, instance=listing)
        image_form = ListingImagesEditForm(request.POST, request.FILES, listing=listing)
        if form.is_valid() and image_form.is_valid():
            listing = form.save()

            listing_images = {image.id: image for image in listing.images.all()}

            for image_id in image_form.delete_ids:
                listing_images[image_id].delete()
                listing_images.pop(image_id, None)

            ordered_existing = []
            seen_ids = set()
            for image_id in image_form.ordering_ids:
                if image_id in listing_images and image_id not in seen_ids:
                    ordered_existing.append(listing_images[image_id])
                    seen_ids.add(image_id)

            remaining_existing = [
                image
                for image in listing.images.exclude(id__in=image_form.delete_ids).order_by("position", "id")
                if image.id not in seen_ids
            ]
            final_images = ordered_existing + remaining_existing

            for new_image in image_form.new_images:
                final_images.append(listing.images.create(image=new_image, position=0))

            for index, image in enumerate(final_images):
                if image.position != index:
                    image.position = index
                    image.save(update_fields=["position"])

            first_image = listing.images.order_by("position", "id").first()
            listing.image = first_image.image if first_image else None
            listing.save(update_fields=["image", "updated_at"])

            messages.success(request, "Обявата е редактирана успешно.")
            return redirect("marketplace-my-listings-page")
    else:
        form = ListingEditForm(instance=listing)

    return render(
        request,
        "marketplace/edit_listing.html",
        {
            "form": form,
            "image_form": image_form,
            "listing": listing,
            "existing_images_json": json.dumps([
                {"id": image.id, "url": image.image.url}
                for image in listing.images.order_by("position", "id")
            ]),
        },
    )


@login_required
def edit_listing_images_page(request, listing_id):
    listing = get_object_or_404(Listing.objects.select_related("owner").prefetch_related("images"), pk=listing_id)
    if listing.owner_id != request.user.id:
        return HttpResponseForbidden("Нямаш достъп да редактираш снимките на тази обява.")

    if request.method == "POST":
        form = ListingImagesEditForm(request.POST, request.FILES, listing=listing)
        if form.is_valid():
            listing_images = {image.id: image for image in listing.images.all()}

            for image_id in form.delete_ids:
                listing_images[image_id].delete()
                listing_images.pop(image_id, None)

            ordered_existing = []
            seen_ids = set()
            for image_id in form.ordering_ids:
                if image_id in listing_images and image_id not in seen_ids:
                    ordered_existing.append(listing_images[image_id])
                    seen_ids.add(image_id)

            remaining_existing = [
                image
                for image in listing.images.exclude(id__in=form.delete_ids).order_by("position", "id")
                if image.id not in seen_ids
            ]
            final_images = ordered_existing + remaining_existing

            for new_image in form.new_images:
                final_images.append(listing.images.create(image=new_image, position=0))

            for index, image in enumerate(final_images):
                if image.position != index:
                    image.position = index
                    image.save(update_fields=["position"])

            first_image = listing.images.order_by("position", "id").first()
            listing.image = first_image.image if first_image else None
            listing.save(update_fields=["image", "updated_at"])

            messages.success(request, "Снимките на обявата са обновени успешно.")
            return redirect("marketplace-edit-images-page", listing_id=listing.id)
    else:
        form = ListingImagesEditForm(listing=listing)

    return render(
        request,
        "marketplace/edit_listing_images.html",
        {
            "listing": listing,
            "form": form,
            "existing_images_json": json.dumps([
                {"id": image.id, "url": image.image.url}
                for image in listing.images.order_by("position", "id")
            ]),
        },
    )


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
