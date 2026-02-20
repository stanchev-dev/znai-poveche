from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Report
from .serializers import (
    AdminActionSerializer,
    ReportAdminListSerializer,
    ReportCreateSerializer,
)


class AdminReportPagination(PageNumberPagination):
    page_size = 20


class ReportCreateAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReportCreateSerializer
    renderer_classes = [JSONRenderer]


class AdminReportListAPIView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ReportAdminListSerializer
    pagination_class = AdminReportPagination
    renderer_classes = [JSONRenderer]
    queryset = Report.objects.select_related("reporter", "content_type")


class AdminActionsAPIView(APIView):
    permission_classes = [IsAdminUser]
    renderer_classes = [JSONRenderer]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = AdminActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        report = get_object_or_404(Report, pk=serializer.validated_data["report_id"])

        if action == AdminActionSerializer.ACTION_SET_STATUS:
            return self._set_status(report, serializer.validated_data["status"])
        if action == AdminActionSerializer.ACTION_DELETE_TARGET:
            return self._delete_target(report)
        return self._suspend_user(report)

    def _set_status(self, report, new_status):
        report.status = new_status
        if new_status in {Report.STATUS_RESOLVED, Report.STATUS_REJECTED}:
            report.resolved_at = timezone.now()
        else:
            report.resolved_at = None
        report.save(update_fields=["status", "resolved_at"])
        return Response(ReportAdminListSerializer(report).data)

    def _delete_target(self, report):
        target = report.target
        if target is not None:
            target.delete()
        resolved_at = timezone.now()
        Report.objects.filter(pk=report.pk).update(
            status=Report.STATUS_RESOLVED,
            resolved_at=resolved_at,
        )
        report.status = Report.STATUS_RESOLVED
        report.resolved_at = resolved_at
        return Response(
            {"success": True, "report_id": report.id},
            status=status.HTTP_200_OK,
        )

    def _suspend_user(self, report):
        target = report.target
        if target is None:
            return Response(
                {"detail": _("Целевото съдържание за този сигнал не е намерено.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_author = target.author
        if target_author.is_staff or target_author.is_superuser:
            return Response(
                {
                    "detail": _("Не можеш да спреш staff или superuser акаунти."),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_author.is_active = False
        target_author.save(update_fields=["is_active"])

        report.status = Report.STATUS_RESOLVED
        report.resolved_at = timezone.now()
        report.save(update_fields=["status", "resolved_at"])

        return Response(
            {
                "success": True,
                "report_id": report.id,
                "suspended_user": {
                    "id": target_author.id,
                    "username": target_author.username,
                },
            },
            status=status.HTTP_200_OK,
        )
