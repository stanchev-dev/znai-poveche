from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.common.images import process_image, validate_image_upload

from .models import Comment, Post, Subject


User = get_user_model()


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "slug", "theme_color", "tile_image"]


class AuthorSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source="profile.display_name")
    level = serializers.IntegerField(source="profile.level")

    class Meta:
        model = User
        fields = ["username", "display_name", "level"]


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
