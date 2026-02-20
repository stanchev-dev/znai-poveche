from django.contrib import admin, messages
from django.utils import timezone

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "reporter",
        "target_display",
        "reason",
        "status",
    )
    list_filter = ("created_at", "content_type", "reason", "status")
    search_fields = (
        "reporter__username",
        "reporter__email",
        "reason",
        "object_id",
    )
    autocomplete_fields = ("reporter",)
    actions = ("delete_target_content", "mark_as_resolved")

    @admin.display(description="Target")
    def target_display(self, obj):
        model_name = obj.content_type.model if obj.content_type_id else "unknown"
        return f"{model_name} #{obj.object_id}"

    @admin.action(description="Delete target content")
    def delete_target_content(self, request, queryset):
        deleted_count = 0
        missing_count = 0
        resolved_at = timezone.now()

        for report in queryset:
            target_pk = report.object_id
            target = report.target
            if target is None:
                missing_count += 1
                continue

            target.delete()
            deleted_count += 1

            if hasattr(report, "status"):
                Report.objects.filter(pk=report.pk, object_id=target_pk).update(
                    status=Report.STATUS_RESOLVED,
                    resolved_at=resolved_at,
                )

        if deleted_count:
            self.message_user(
                request,
                f"Deleted target content for {deleted_count} report(s).",
                level=messages.SUCCESS,
            )
        if missing_count:
            self.message_user(
                request,
                f"Target not found for {missing_count} report(s).",
                level=messages.WARNING,
            )

    @admin.action(description="Mark as resolved")
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(
            status=Report.STATUS_RESOLVED,
            resolved_at=timezone.now(),
        )
        self.message_user(
            request,
            f"Marked {updated} report(s) as resolved.",
            level=messages.SUCCESS,
        )
