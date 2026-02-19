from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.common.images import process_image, validate_image_upload
from apps.common.utils import (
    FALLBACK_DARK_COLOR,
    FALLBACK_LIGHT_COLOR,
    lighten_hex,
    normalize_hex,
)

from .models import Comment, Post, Subject


User = get_user_model()


class SubjectSerializer(serializers.ModelSerializer):
    theme_color = serializers.SerializerMethodField()
    theme_color_dark = serializers.SerializerMethodField()
    theme_color_light = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            "id",
            "name",
            "slug",
            "theme_color",
            "theme_color_dark",
            "theme_color_light",
            "tile_image",
        ]

    def get_theme_color(self, obj: Subject) -> str:
        return normalize_hex(obj.theme_color) or FALLBACK_DARK_COLOR

    def get_theme_color_dark(self, obj: Subject) -> str:
        return normalize_hex(obj.theme_color) or FALLBACK_DARK_COLOR

    def get_theme_color_light(self, obj: Subject) -> str:
        normalized = normalize_hex(obj.theme_color)
        if not normalized:
            return FALLBACK_LIGHT_COLOR
        return lighten_hex(normalized, 0.532)


class AuthorSerializer(serializers.ModelSerializer):
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


class SubjectSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["slug", "name"]


class PostListSerializer(serializers.ModelSerializer):
    subject = SubjectSummarySerializer()
    author = AuthorSerializer()
    excerpt = serializers.SerializerMethodField()
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "subject",
            "title",
            "excerpt",
            "score",
            "author",
            "created_at",
            "image",
        ]

    def get_excerpt(self, obj: Post) -> str:
        return obj.body[:160]


class PostDetailSerializer(serializers.ModelSerializer):
    subject = SubjectSummarySerializer()
    author = AuthorSerializer()
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "subject",
            "title",
            "body",
            "score",
            "author",
            "created_at",
            "updated_at",
            "image",
        ]


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "body",
            "score",
            "author",
            "created_at",
            "image",
        ]


class PostCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    subject = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Subject.objects.all(),
    )
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Post
        fields = ["id", "subject", "title", "body", "image"]

    def validate_title(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value

    def validate_body(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Body cannot be empty.")
        return value

    def validate_image(self, value):
        if value is None:
            return value
        validate_image_upload(value)
        return value

    def create(self, validated_data):
        image = validated_data.get("image")
        if image is not None:
            validated_data["image"] = process_image(
                image,
                max_side=1600,
                quality=80,
            )
        return super().create(validated_data)


class CommentCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Comment
        fields = ["id", "body", "image"]

    def validate_body(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Body cannot be empty.")
        return value

    def validate_image(self, value):
        if value is None:
            return value
        validate_image_upload(value)
        return value

    def create(self, validated_data):
        image = validated_data.get("image")
        if image is not None:
            validated_data["image"] = process_image(
                image,
                max_side=1600,
                quality=80,
            )
        return super().create(validated_data)


class VoteInputSerializer(serializers.Serializer):
    value = serializers.ChoiceField(choices=[1, -1])
