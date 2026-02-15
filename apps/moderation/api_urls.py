from django.urls import path

from .api_views import (
    AdminActionsAPIView,
    AdminReportListAPIView,
    ReportCreateAPIView,
)

urlpatterns = [
    path("reports/", ReportCreateAPIView.as_view(), name="report-create"),
    path(
        "admin/reports/",
        AdminReportListAPIView.as_view(),
        name="admin-report-list",
    ),
    path("admin/actions/", AdminActionsAPIView.as_view(), name="admin-actions"),
]
