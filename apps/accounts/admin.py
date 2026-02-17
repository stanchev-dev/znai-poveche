from django.contrib import admin
from django.utils import timezone

from apps.accounts.models import Profile, TeacherVerificationRequest


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "display_name",
        "reputation_points",
        "max_level_reached",
        "is_verified_teacher",
    )
    search_fields = ("user__username", "display_name")


@admin.register(TeacherVerificationRequest)
class TeacherVerificationRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "created_at", "decided_at")
    list_filter = ("status",)
    search_fields = ("user__email", "user__username")
    actions = ("approve_requests", "reject_requests")

    @admin.action(description="Approve selected verification requests")
    def approve_requests(self, request, queryset):
        now = timezone.now()
        for verification in queryset.select_related("user__profile"):
            verification.status = TeacherVerificationRequest.Status.APPROVED
            verification.decided_at = now
            verification.save(update_fields=["status", "decided_at"])
            profile = verification.user.profile
            if not profile.is_verified_teacher:
                profile.is_verified_teacher = True
                profile.save(update_fields=["is_verified_teacher"])
            if verification.proof_file:
                verification.proof_file.delete(save=False)

    @admin.action(description="Reject selected verification requests")
    def reject_requests(self, request, queryset):
        now = timezone.now()
        for verification in queryset.select_related("user__profile"):
            verification.status = TeacherVerificationRequest.Status.REJECTED
            verification.decided_at = now
            verification.save(update_fields=["status", "decided_at"])
            profile = verification.user.profile
            if profile.is_verified_teacher:
                profile.is_verified_teacher = False
                profile.save(update_fields=["is_verified_teacher"])
            if verification.proof_file:
                verification.proof_file.delete(save=False)
