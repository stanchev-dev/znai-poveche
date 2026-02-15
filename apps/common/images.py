from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework import serializers

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE_BYTES = 2 * 1024 * 1024


def validate_image_upload(uploaded_file) -> None:
    if uploaded_file.size > MAX_IMAGE_SIZE_BYTES:
        raise serializers.ValidationError("Image must be 2MB or smaller.")

    extension = Path(uploaded_file.name or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise serializers.ValidationError(
            "Unsupported image format. Allowed: jpg, jpeg, png, webp."
        )

    try:
        uploaded_file.seek(0)
        with Image.open(uploaded_file) as img:
            img.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise serializers.ValidationError("Upload a valid image file.")
    finally:
        uploaded_file.seek(0)


def _normalize_mode(img: Image.Image) -> Image.Image:
    has_alpha = "A" in img.getbands() or img.mode in {"LA", "PA"}
    if img.mode in {"RGB", "RGBA"}:
        return img
    if has_alpha:
        return img.convert("RGBA")
    return img.convert("RGB")


def process_image(
    uploaded_file,
    *,
    max_side: int = 1600,
    quality: int = 80,
) -> ContentFile:
    uploaded_file.seek(0)
    with Image.open(uploaded_file) as img:
        img.load()
        img = ImageOps.exif_transpose(img)
        img = _normalize_mode(img)
        img.thumbnail((max_side, max_side), resample=Image.Resampling.LANCZOS)

        buffer = BytesIO()
        img.save(
            buffer,
            format="WEBP",
            quality=quality,
            method=6,
            optimize=True,
        )

    buffer.seek(0)
    return ContentFile(buffer.getvalue(), name=f"{uuid4().hex}.webp")
