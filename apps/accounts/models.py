from django.conf import settings
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=50, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    reputation_points = models.IntegerField(default=0)
    max_level_reached = models.PositiveIntegerField(default=1)
    daily_base_points = models.PositiveIntegerField(default=0)
    daily_base_points_date = models.DateField(default=timezone.localdate)
    is_verified_teacher = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.display_name or self.user.get_username()

    @property
    def level(self) -> int:
        return (self.reputation_points // 25) + 1


class TeacherVerificationRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_verification_requests",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    subjects = models.TextField(blank=True)
    school_email = models.EmailField(blank=True)
    school_url = models.URLField(blank=True)
    proof_file = models.FileField(upload_to="verification/", blank=True)
    note = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} ({self.status})"
