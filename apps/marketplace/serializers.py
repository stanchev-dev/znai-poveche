from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework import serializers

from apps.discussions.models import Subject
from apps.common.utils import (
    FALLBACK_DARK_COLOR,
    FALLBACK_LIGHT_COLOR,
    lighten_hex,
    normalize_hex,
)

from .forms import (
    ALLOWED_LISTING_IMAGE_EXTENSIONS,
    MAX_LISTING_IMAGES,
    MAX_LISTING_IMAGE_SIZE_BYTES,
    ListingPublishForm,
)
from .models import Listing, ListingImage


User = get_user_model()


class SubjectSummarySerializer(serializers.ModelSerializer):
    theme_color_dark = serializers.SerializerMethodField()
    theme_color_light = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ["id", "name", "slug", "theme_color_dark", "theme_color_light"]

    def get_theme_color_dark(self, obj: Subject) -> str:
        return normalize_hex(obj.theme_color) or FALLBACK_DARK_COLOR

    def get_theme_color_light(self, obj: Subject) -> str:
        normalized = normalize_hex(obj.theme_color)
        if not normalized:
            return FALLBACK_LIGHT_COLOR
        return lighten_hex(normalized, 0.532)


class OwnerSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    role_label = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["username", "display_name", "level", "role", "role_label"]

    def get_display_name(self, obj) -> str:
        try:
            return obj.profile.display_name or obj.get_username()
        except ObjectDoesNotExist:
            return obj.get_username()

    def get_level(self, obj) -> int:
        try:
            return obj.profile.level
        except ObjectDoesNotExist:
            return 1

    def get_role(self, obj) -> str:
        try:
            return obj.profile.role
        except ObjectDoesNotExist:
            return "learner"

    def get_role_label(self, obj) -> str:
        try:
            return obj.profile.get_role_display()
        except ObjectDoesNotExist:
            return "Учащ"


class ListingImageSerializer(serializers.ModelSerializer):
    is_cover = serializers.SerializerMethodField()

    class Meta:
        model = ListingImage
        fields = ["id", "image", "position", "is_cover"]

    def get_is_cover(self, obj: ListingImage) -> bool:
        return obj.position == 0


class ListingListSerializer(serializers.ModelSerializer):
    subject = SubjectSummarySerializer(read_only=True)
    owner = OwnerSerializer(read_only=True)
    description_excerpt = serializers.SerializerMethodField()
    is_vip = serializers.SerializerMethodField()
    author_role = serializers.SerializerMethodField()
    author_role_label = serializers.SerializerMethodField()
    lesson_mode_label = serializers.CharField(
        source="get_lesson_mode_display",
        read_only=True,
    )
    images = ListingImageSerializer(many=True, read_only=True)

    class Meta:
        model = Listing
        fields = [
            "id",
            "subject",
            "price_per_hour",
            "lesson_mode",
            "lesson_mode_label",
            "image",
            "images",
            "description_excerpt",
            "is_vip",
            "vip_until",
            "created_at",
            "owner",
            "author_role",
            "author_role_label",
        ]

    def get_description_excerpt(self, obj: Listing) -> str:
        return obj.description[:160]

    def get_is_vip(self, obj: Listing) -> bool:
        now = timezone.now()
        return bool(obj.vip_until and obj.vip_until > now)

    def get_author_role(self, obj: Listing) -> str:
        try:
            return obj.owner.profile.role
        except ObjectDoesNotExist:
            return "learner"

    def get_author_role_label(self, obj: Listing) -> str:
        try:
            return obj.owner.profile.get_role_display()
        except ObjectDoesNotExist:
            return "Учащ"


class ListingDetailSerializer(serializers.ModelSerializer):
    subject = SubjectSummarySerializer(read_only=True)
    owner = OwnerSerializer(read_only=True)
    is_vip = serializers.SerializerMethodField()
    author_role = serializers.SerializerMethodField()
    author_role_label = serializers.SerializerMethodField()
    lesson_mode_label = serializers.CharField(
        source="get_lesson_mode_display",
        read_only=True,
    )
    images = ListingImageSerializer(many=True, read_only=True)

    class Meta:
        model = Listing
        fields = [
            "id",
            "subject",
            "price_per_hour",
            "lesson_mode",
            "lesson_mode_label",
            "image",
            "images",
            "description",
            "is_vip",
            "vip_until",
            "created_at",
            "owner",
            "author_role",
            "author_role_label",
        ]

    def get_is_vip(self, obj: Listing) -> bool:
        now = timezone.now()
        return bool(obj.vip_until and obj.vip_until > now)

    def get_author_role(self, obj: Listing) -> str:
        try:
            return obj.owner.profile.role
        except ObjectDoesNotExist:
            return "learner"

    def get_author_role_label(self, obj: Listing) -> str:
        try:
            return obj.owner.profile.get_role_display()
        except ObjectDoesNotExist:
            return "Учащ"


class ListingCreateSerializer(serializers.ModelSerializer):
    subject = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Subject.objects.all(),
    )
    contact_email = serializers.EmailField(
        required=False,
        allow_blank=True,
    )
    contact_url = serializers.URLField(
        required=False,
        allow_blank=True,
    )
    image = serializers.ImageField(required=False, allow_null=True)
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        allow_empty=True,
        write_only=True,
    )

    class Meta:
        model = Listing
        fields = [
            "subject",
            "price_per_hour",
            "lesson_mode",
            "image",
            "images",
            "description",
            "contact_name",
            "contact_phone",
            "contact_email",
            "contact_url",
        ]

    def validate_images(self, value):
        if len(value) > MAX_LISTING_IMAGES:
            raise serializers.ValidationError(
                f"Можеш да качиш до {MAX_LISTING_IMAGES} снимки."
            )

        for image in value:
            extension = Path(image.name or "").suffix.lower()
            if extension not in ALLOWED_LISTING_IMAGE_EXTENSIONS:
                raise serializers.ValidationError(
                    "Невалиден файл. Приемаме само jpg, jpeg, png до 2MB."
                )
            if image.size > MAX_LISTING_IMAGE_SIZE_BYTES:
                raise serializers.ValidationError(
                    "Невалиден файл. Приемаме само jpg, jpeg, png до 2MB."
                )

        return value

    def validate_price_per_hour(self, value):
        if isinstance(value, str):
            return value.replace(",", ".")
        return value

    def validate(self, attrs):
        attrs.setdefault("contact_email", "")
        attrs.setdefault("contact_url", "")

        form = ListingPublishForm(
            data={
                "subject": self.initial_data.get("subject", ""),
                "price_per_hour": attrs.get("price_per_hour"),
                "lesson_mode": attrs.get("lesson_mode"),
                "description": attrs.get("description"),
                "contact_name": attrs.get("contact_name"),
                "contact_phone": attrs.get("contact_phone"),
                "contact_email": attrs.get("contact_email"),
            }
        )
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        cleaned_data = form.cleaned_data
        attrs["price_per_hour"] = cleaned_data["price_per_hour"]
        attrs["lesson_mode"] = cleaned_data["lesson_mode"]
        attrs["description"] = cleaned_data["description"]
        attrs["contact_name"] = cleaned_data["contact_name"]
        attrs["contact_phone"] = cleaned_data["contact_phone"]
        attrs["contact_email"] = (cleaned_data.get("contact_email") or "").strip()
        attrs["contact_url"] = (attrs.get("contact_url") or "").strip()

        image_files = []
        legacy_image = attrs.get("image")
        if legacy_image is not None:
            image_files.append(legacy_image)
        image_files.extend(attrs.get("images", []))

        if len(image_files) > MAX_LISTING_IMAGES:
            raise serializers.ValidationError(
                {"images": [f"Можеш да качиш до {MAX_LISTING_IMAGES} снимки."]}
            )

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        uploaded_images = validated_data.pop("images", [])
        legacy_image = validated_data.pop("image", None)

        validated_data.setdefault("contact_name", "")
        validated_data.setdefault("contact_email", "")
        validated_data.setdefault("contact_url", "")

        listing = Listing.objects.create(
            owner=request.user,
            **validated_data,
        )

        image_files = []
        if legacy_image is not None:
            image_files.append(legacy_image)
        image_files.extend(uploaded_images)

        for position, image in enumerate(image_files):
            ListingImage.objects.create(
                listing=listing,
                image=image,
                position=position,
            )

        if image_files:
            listing.image = listing.images.order_by("position", "id").first().image
            listing.save(update_fields=["image", "updated_at"])

        return listing


class ListingContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ["contact_name", "contact_phone", "contact_email", "contact_url"]


class ListingVipUpgradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ["vip_until"]

    def validate_vip_until(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("vip_until must be in the future.")
        return value
