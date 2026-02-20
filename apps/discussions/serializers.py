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

from .models import Comment, Post, PostImage, Subject


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
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "display_name", "level", "role", "role_label", "avatar"]

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

    def get_avatar(self, obj) -> str | None:
        try:
            avatar = obj.profile.avatar
            return avatar.url if avatar else None
        except ObjectDoesNotExist:
            return None


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
            "grade",
            "author",
            "created_at",
            "image",
        ]

    def get_excerpt(self, obj: Post) -> str:
        return obj.body[:160]




class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ["id", "image", "position"]


class PostDetailSerializer(serializers.ModelSerializer):
    subject = SubjectSummarySerializer()
    author = AuthorSerializer()
    image = serializers.ImageField(read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    user_vote = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "subject",
            "title",
            "body",
            "score",
            "grade",
            "author",
            "created_at",
            "updated_at",
            "image",
            "images",
            "user_vote",
        ]


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()
    image = serializers.ImageField(read_only=True)
    user_vote = serializers.IntegerField(read_only=True)
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "body",
            "score",
            "author",
            "created_at",
            "image",
            "user_vote",
            "can_delete",
        ]

    def get_can_delete(self, obj: Comment) -> bool:
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return (
            obj.author_id == request.user.id
            or request.user.is_staff
            or request.user.is_superuser
        )


class PostCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    subject = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Subject.objects.all(),
    )
    image = serializers.ImageField(required=False, allow_null=True)
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        allow_empty=True,
        write_only=True,
    )

    class Meta:
        model = Post
        fields = ["id", "subject", "title", "body", "grade", "image", "images"]

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

    def validate_images(self, value):
        for image in value:
            validate_image_upload(image)
        return value

    def create(self, validated_data):
        images = validated_data.pop("images", [])
        image = validated_data.get("image")
        if image is not None:
            validated_data["image"] = process_image(
                image,
                max_side=1600,
                quality=80,
            )
        post = super().create(validated_data)

        for index, uploaded_image in enumerate(images):
            PostImage.objects.create(
                post=post,
                image=process_image(uploaded_image, max_side=1600, quality=80),
                position=index,
            )

        return post




class PostBodyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["body"]

    def validate_body(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Body cannot be empty.")
        return value


class CommentCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "body"]

    def validate_body(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Body cannot be empty.")
        return value

    def validate(self, attrs):
        if "image" in self.initial_data:
            raise serializers.ValidationError(
                {"image": "Снимки към коментари не са позволени."}
            )
        return super().validate(attrs)


class VoteInputSerializer(serializers.Serializer):
    value = serializers.ChoiceField(choices=[1, -1, 0])
