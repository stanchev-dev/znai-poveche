from django import forms
from django.contrib import admin

from .models import Comment, Post, Subject


class SubjectAdminForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = "__all__"

    def clean_theme_color(self):
        value = (self.cleaned_data.get("theme_color") or "").strip()
        if not value:
            return ""
        if not value.startswith("#"):
            value = f"#{value}"
        return value.upper()


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    form = SubjectAdminForm
    list_display = ("name", "sort_order", "theme_color", "slug")
    list_editable = ("sort_order", "theme_color")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("sort_order", "name")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "subject", "author", "score", "created_at")
    list_filter = ("subject", "created_at")
    search_fields = ("title", "body", "author__username")
    autocomplete_fields = ("subject", "author")
    exclude = ("score",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "author", "score", "created_at")
    list_filter = ("created_at",)
    search_fields = ("body", "author__username")
    autocomplete_fields = ("post", "author")
    exclude = ("score",)
