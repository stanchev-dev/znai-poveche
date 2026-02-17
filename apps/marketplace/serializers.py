from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework import serializers

from .models import Listing
from apps.discussions.models import Subject


User = get_user_model()


class SubjectSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "slug"]


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


class ListingListSerializer(serializers.ModelSerializer):
    subject = SubjectSummarySerializer(read_only=True)
    owner = OwnerSerializer(read_only=True)
    description_excerpt = serializers.SerializerMethodField()
    is_vip = serializers.SerializerMethodField()
    author_role = serializers.SerializerMethodField()
    author_role_label = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            "id",
            "subject",
            "price_per_hour",
            "online_only",
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

    class Meta:
        model = Listing
        fields = [
            "id",
            "subject",
            "price_per_hour",
            "online_only",
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

    class Meta:
        model = Listing
        fields = [
            "subject",
            "price_per_hour",
            "online_only",
            "description",
            "contact_phone",
            "contact_email",
            "contact_url",
        ]

    def validate(self, attrs):
        contact_phone = attrs.get("contact_phone", "")
        contact_email = attrs.get("contact_email", "")
        contact_url = attrs.get("contact_url", "")

        attrs.setdefault("contact_email", "")
        attrs.setdefault("contact_url", "")

        contact_phone = (contact_phone or "").strip()
        contact_email = (contact_email or "").strip()
        contact_url = (contact_url or "").strip()

        attrs["contact_phone"] = contact_phone
        attrs["contact_email"] = contact_email
        attrs["contact_url"] = contact_url

        if not (contact_phone or contact_email or contact_url):
            raise serializers.ValidationError(
                "Моля, добавете поне един контакт: телефон, имейл или линк."
            )

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data.setdefault("contact_email", "")
        validated_data.setdefault("contact_url", "")
        return Listing.objects.create(
            owner=request.user,
            **validated_data,
        )


class ListingContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ["contact_phone", "contact_email", "contact_url"]


class ListingVipUpgradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ["vip_until"]

    def validate_vip_until(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("vip_until must be in the future.")
        return value
