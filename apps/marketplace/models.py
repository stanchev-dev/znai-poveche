from django.conf import settings
from django.db import models


class Listing(models.Model):
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
    online_only = models.BooleanField(default=False)
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
