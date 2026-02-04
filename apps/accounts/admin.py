from django.contrib import admin

from apps.accounts.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "reputation_points", "max_level_reached")
    search_fields = ("user__username", "display_name")
