from django.conf import settings
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    class Role(models.TextChoices):
        LEARNER = "learner", "Учащ"
        TEACHER = "teacher", "Учител"

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
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.LEARNER,
    )

    def __str__(self) -> str:
        return self.display_name or self.user.get_username()

    @property
    def level(self) -> int:
        return (self.reputation_points // 25) + 1
