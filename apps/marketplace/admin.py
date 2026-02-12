from django.contrib import admin

from .models import Listing


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subject",
        "owner",
        "price_per_hour",
        "online_only",
        "vip_until",
        "created_at",
    )
    list_filter = ("online_only", "subject", "created_at", "vip_until")
    search_fields = (
        "owner__username",
        "owner__email",
        "subject__name",
        "description",
    )
    ordering = ("-created_at",)
