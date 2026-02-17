from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import models
from uuid import uuid4

from apps.common.images import process_image, validate_image_upload


def listing_image_upload_to(instance, filename):
    return f"listings/{uuid4().hex}.webp"


class Listing(models.Model):
    class LessonMode(models.TextChoices):
        ONLINE = "online", "Онлайн"
        IN_PERSON = "in_person", "Присъствено"
        ONLINE_AND_IN_PERSON = "online_and_in_person", "Онлайн + присъствено"

    subject = models.ForeignKey(
        "discussions.Subject",
        on_delete=models.PROTECT,
        related_name="listings",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listings",
    )
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2)
    lesson_mode = models.CharField(
        max_length=24,
        choices=LessonMode.choices,
        default=LessonMode.ONLINE_AND_IN_PERSON,
    )
    image = models.ImageField(
        upload_to=listing_image_upload_to,
        blank=True,
        null=True,
    )
    description = models.TextField()
    contact_phone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True, default="")
    contact_url = models.URLField(blank=True, default="")
    vip_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Listing #{self.pk} by {self.owner_id}"

    def save(self, *args, **kwargs):
        if (
            self.image
            and getattr(self.image, "_committed", True) is False
            and isinstance(getattr(self.image, "file", None), UploadedFile)
        ):
            validate_image_upload(self.image)
            self.image = process_image(self.image, max_side=1600, quality=80)
        super().save(*args, **kwargs)
