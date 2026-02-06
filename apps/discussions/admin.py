from django.contrib import admin

from .models import Comment, Post, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "subject", "author", "score", "created_at")
    list_filter = ("subject", "created_at")
    search_fields = ("title", "body", "author__username")
    autocomplete_fields = ("subject", "author")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "author", "score", "created_at")
    list_filter = ("created_at",)
    search_fields = ("body", "author__username")
    autocomplete_fields = ("post", "author")
