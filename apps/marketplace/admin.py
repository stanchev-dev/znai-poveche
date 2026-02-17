from django.contrib import admin

from .models import Listing


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
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
