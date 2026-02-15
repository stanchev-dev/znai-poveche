from uuid import uuid4

from django.conf import settings
from django.db import models
from django.core.files.uploadedfile import UploadedFile
from django.utils.text import slugify

from apps.common.images import process_image, validate_image_upload


def post_image_upload_to(instance, filename):
    return f"posts/{uuid4().hex}.webp"


def comment_image_upload_to(instance, filename):
    return f"comments/{uuid4().hex}.webp"


class Subject(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Post(models.Model):
    subject = models.ForeignKey(
        "Subject",
        on_delete=models.PROTECT,
        related_name="posts",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    title = models.CharField(max_length=120)
    body = models.TextField()
    image = models.ImageField(
        upload_to=post_image_upload_to,
        blank=True,
        null=True,
    )
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if (
            self.image
            and getattr(self.image, "_committed", True) is False
            and isinstance(getattr(self.image, "file", None), UploadedFile)
        ):
            validate_image_upload(self.image)
            self.image = process_image(self.image, max_side=1600, quality=80)
        super().save(*args, **kwargs)


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    body = models.TextField()
    image = models.ImageField(
        upload_to=comment_image_upload_to,
        blank=True,
        null=True,
    )
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Comment #{self.id} on {self.post_id}"

    def save(self, *args, **kwargs):
        if (
            self.image
            and getattr(self.image, "_committed", True) is False
            and isinstance(getattr(self.image, "file", None), UploadedFile)
        ):
            validate_image_upload(self.image)
            self.image = process_image(self.image, max_side=1600, quality=80)
        super().save(*args, **kwargs)


class PostVote(models.Model):
    UPVOTE = 1
    DOWNVOTE = -1
    VOTE_CHOICES = (
        (UPVOTE, "Upvote"),
        (DOWNVOTE, "Downvote"),
    )

    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_votes",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    value = models.SmallIntegerField(choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["voter", "post"],
                name="unique_post_vote_per_user",
            ),
        ]

    def __str__(self) -> str:
        return f"PostVote {self.value} by {self.voter_id} on {self.post_id}"


class CommentVote(models.Model):
    UPVOTE = 1
    DOWNVOTE = -1
    VOTE_CHOICES = (
        (UPVOTE, "Upvote"),
        (DOWNVOTE, "Downvote"),
    )

    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comment_votes",
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    value = models.SmallIntegerField(choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["voter", "comment"],
                name="unique_comment_vote_per_user",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"CommentVote {self.value} by {self.voter_id} on {self.comment_id}"
        )
