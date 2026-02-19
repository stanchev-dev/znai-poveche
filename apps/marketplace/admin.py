from django.contrib import admin

from .models import Listing, ListingImage


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 0
    fields = ("image", "position")
    ordering = ("position", "id")


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    inlines = [ListingImageInline]
    list_display = (
        "id",
        "subject",
        "owner",
        "price_per_hour",
        "lesson_mode",
        "vip_until",
        "created_at",
    )
    list_filter = ("lesson_mode", "subject", "created_at", "vip_until")
    search_fields = (
        "owner__username",
        "owner__email",
        "subject__name",
        "description",
    )
    ordering = ("-created_at",)

    def get_inline_instances(self, request, obj=None):
        if request.method == "POST" and "images-TOTAL_FORMS" not in request.POST:
            return []
        return super().get_inline_instances(request, obj)
