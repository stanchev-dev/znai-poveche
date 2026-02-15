from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q


class ReportStatus(models.TextChoices):
    OPEN = "open", "Open"
    REVIEWING = "reviewing", "Reviewing"
    RESOLVED = "resolved", "Resolved"
    REJECTED = "rejected", "Rejected"


class Report(models.Model):
    REASON_SPAM = "spam"
    REASON_ABUSE = "abuse"
    REASON_OFF_TOPIC = "off_topic"
    REASON_OTHER = "other"
    REASON_CHOICES = [
        (REASON_SPAM, "Spam"),
        (REASON_ABUSE, "Abuse"),
        (REASON_OFF_TOPIC, "Off topic"),
        (REASON_OTHER, "Other"),
    ]

    STATUS_OPEN = ReportStatus.OPEN
    STATUS_REVIEWING = ReportStatus.REVIEWING
    STATUS_RESOLVED = ReportStatus.RESOLVED
    STATUS_REJECTED = ReportStatus.REJECTED
    STATUS_CHOICES = ReportStatus.choices

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_made",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey("content_type", "object_id")
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=ReportStatus.choices,
        default=ReportStatus.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["reporter", "content_type", "object_id"],
                condition=Q(status__in=[ReportStatus.OPEN, ReportStatus.REVIEWING]),
                name="uniq_open_reviewing_report",
            ),
        ]

    def __str__(self) -> str:
        return f"Report #{self.pk} by {self.reporter_id}"
