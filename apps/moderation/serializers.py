from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from apps.discussions.models import Comment, Post
from apps.marketplace.models import Listing

from .models import Report

User = get_user_model()

TARGET_MODEL_MAP = {
    "post": Post,
    "comment": Comment,
    "listing": Listing,
}


class ReportCreateSerializer(serializers.ModelSerializer):
    target_type = serializers.ChoiceField(choices=list(TARGET_MODEL_MAP.keys()), write_only=True)
    target_id = serializers.IntegerField(write_only=True, min_value=1)

    class Meta:
        model = Report
        fields = [
            "id",
            "target_type",
            "target_id",
            "reason",
            "message",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]

    def validate(self, attrs):
        target_type = attrs["target_type"]
        target_id = attrs["target_id"]

        model_class = TARGET_MODEL_MAP.get(target_type)
        if not model_class:
            raise serializers.ValidationError(
                {"target_type": [_("Невалиден тип на съдържанието.")]}
            )

        try:
            target = model_class.objects.get(pk=target_id)
        except model_class.DoesNotExist as exc:
            raise NotFound(detail=_("Целевото съдържание не е намерено.")) from exc

        reporter = self.context["request"].user
        content_type = ContentType.objects.get_for_model(model_class)
        duplicate_exists = Report.objects.filter(
            reporter=reporter,
            content_type=content_type,
            object_id=target.pk,
            status__in=[Report.STATUS_OPEN, Report.STATUS_REVIEWING],
        ).exists()
        if duplicate_exists:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _("Вече имаш отворен/преглеждан сигнал за това съдържание.")
                    ]
                }
            )

        attrs["target"] = target
        attrs["content_type"] = content_type
        return attrs

    def create(self, validated_data):
        target = validated_data.pop("target")
        validated_data.pop("target_type")
        validated_data.pop("target_id")
        return Report.objects.create(
            reporter=self.context["request"].user,
            content_type=validated_data["content_type"],
            object_id=target.pk,
            reason=validated_data["reason"],
            message=validated_data.get("message", ""),
            status=Report.STATUS_OPEN,
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        model_name = instance.content_type.model
        data["target_type"] = model_name if model_name in TARGET_MODEL_MAP else "comment"
        data["target_id"] = instance.object_id
        return data


class ReporterSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class ReportAdminListSerializer(serializers.ModelSerializer):
    reporter = ReporterSummarySerializer(read_only=True)
    target_type = serializers.SerializerMethodField()
    target_id = serializers.IntegerField(source="object_id", read_only=True)
    target_preview = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "id",
            "reporter",
            "target_type",
            "target_id",
            "reason",
            "message",
            "status",
            "created_at",
            "resolved_at",
            "target_preview",
        ]

    def get_target_type(self, obj):
        model_name = obj.content_type.model
        return model_name if model_name in TARGET_MODEL_MAP else "comment"

    def get_target_preview(self, obj):
        target = obj.target
        if target is None:
            return None
        if isinstance(target, Post):
            return target.title
        if isinstance(target, Listing):
            return target.description[:80]
        return target.body[:80]


class AdminActionSerializer(serializers.Serializer):
    ACTION_SET_STATUS = "set_status"
    ACTION_DELETE_TARGET = "delete_target"
    ACTION_SUSPEND_USER = "suspend_user"

    ACTION_CHOICES = [
        ACTION_SET_STATUS,
        ACTION_DELETE_TARGET,
        ACTION_SUSPEND_USER,
    ]

    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    report_id = serializers.IntegerField(min_value=1)
    status = serializers.ChoiceField(
        choices=[value for value, _ in Report.STATUS_CHOICES],
        required=False,
    )
    suspend_days = serializers.IntegerField(min_value=1, required=False)

    def validate(self, attrs):
        action = attrs["action"]
        if action == self.ACTION_SET_STATUS and "status" not in attrs:
            raise serializers.ValidationError(
                {"status": [_("Това поле е задължително за действието set_status.")]}
            )
        if action == self.ACTION_SUSPEND_USER and "suspend_days" not in attrs:
            raise serializers.ValidationError(
                {"suspend_days": [_("Това поле е задължително за действието suspend_user.")]}
            )
        return attrs
