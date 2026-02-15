from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.discussions.models import Comment, Post, Subject

from .models import Report

User = get_user_model()


class ModerationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reporter",
            password="testpass123",
        )
        self.admin = User.objects.create_user(
            username="staff",
            password="testpass123",
            is_staff=True,
        )
        self.author = User.objects.create_user(
            username="author",
            password="testpass123",
        )
        self.subject = Subject.objects.create(name="Moderation")
        self.post = Post.objects.create(
            subject=self.subject,
            author=self.author,
            title="Reported post",
            body="Post body for moderation tests.",
        )
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.author,
            body="Comment body for moderation tests.",
        )

    def test_guest_cannot_create_report(self):
        response = self.client.post(
            reverse("report-create"),
            {
                "target_type": "post",
                "target_id": self.post.id,
                "reason": Report.REASON_SPAM,
            },
            format="json",
        )
        self.assertIn(
            response.status_code,
            {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN},
        )

    def test_authenticated_user_can_report_post(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("report-create"),
            {
                "target_type": "post",
                "target_id": self.post.id,
                "reason": Report.REASON_ABUSE,
                "message": "Spam content.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Report.STATUS_OPEN)

    def test_reporting_non_existent_target_returns_404(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("report-create"),
            {
                "target_type": "post",
                "target_id": 999999,
                "reason": Report.REASON_OTHER,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reporting_invalid_target_type_returns_400(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("report-create"),
            {
                "target_type": "listing",
                "target_id": 1,
                "reason": Report.REASON_OTHER,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_open_or_reviewing_report_returns_400(self):
        self.client.force_authenticate(self.user)
        content_type = ContentType.objects.get_for_model(Post)
        Report.objects.create(
            reporter=self.user,
            content_type=content_type,
            object_id=self.post.id,
            reason=Report.REASON_SPAM,
            status=Report.STATUS_OPEN,
        )

        response = self.client.post(
            reverse("report-create"),
            {
                "target_type": "post",
                "target_id": self.post.id,
                "reason": Report.REASON_ABUSE,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_create_new_report_after_previous_is_resolved(self):
        self.client.force_authenticate(self.user)
        first_response = self.client.post(
            reverse("report-create"),
            {
                "target_type": "post",
                "target_id": self.post.id,
                "reason": Report.REASON_ABUSE,
            },
            format="json",
        )
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        first_report_id = first_response.data["id"]

        self.client.force_authenticate(self.admin)
        resolve_response = self.client.post(
            reverse("admin-actions"),
            {
                "action": "set_status",
                "report_id": first_report_id,
                "status": Report.STATUS_RESOLVED,
            },
            format="json",
        )
        self.assertEqual(resolve_response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(self.user)
        second_response = self.client.post(
            reverse("report-create"),
            {
                "target_type": "post",
                "target_id": self.post.id,
                "reason": Report.REASON_SPAM,
            },
            format="json",
        )
        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        second_report_id = second_response.data["id"]

        self.assertNotEqual(first_report_id, second_report_id)

    def test_guest_cannot_access_admin_endpoints(self):
        reports_response = self.client.get(reverse("admin-report-list"))
        actions_response = self.client.post(
            reverse("admin-actions"),
            {"action": "set_status", "report_id": 1, "status": "open"},
            format="json",
        )
        self.assertIn(
            reports_response.status_code,
            {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN},
        )
        self.assertIn(
            actions_response.status_code,
            {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN},
        )

    def test_admin_can_list_reports_with_pagination(self):
        content_type = ContentType.objects.get_for_model(Post)
        Report.objects.create(
            reporter=self.user,
            content_type=content_type,
            object_id=self.post.id,
            reason=Report.REASON_SPAM,
        )
        self.client.force_authenticate(self.admin)

        response = self.client.get(reverse("admin-report-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)

    def test_admin_set_status_updates_resolved_at(self):
        content_type = ContentType.objects.get_for_model(Post)
        report = Report.objects.create(
            reporter=self.user,
            content_type=content_type,
            object_id=self.post.id,
            reason=Report.REASON_SPAM,
        )
        self.client.force_authenticate(self.admin)

        reviewing_response = self.client.post(
            reverse("admin-actions"),
            {
                "action": "set_status",
                "report_id": report.id,
                "status": Report.STATUS_REVIEWING,
            },
            format="json",
        )
        self.assertEqual(reviewing_response.status_code, status.HTTP_200_OK)
        report.refresh_from_db()
        self.assertEqual(report.status, Report.STATUS_REVIEWING)
        self.assertIsNone(report.resolved_at)

        resolved_response = self.client.post(
            reverse("admin-actions"),
            {
                "action": "set_status",
                "report_id": report.id,
                "status": Report.STATUS_RESOLVED,
            },
            format="json",
        )
        self.assertEqual(resolved_response.status_code, status.HTTP_200_OK)
        report.refresh_from_db()
        self.assertEqual(report.status, Report.STATUS_RESOLVED)
        self.assertIsNotNone(report.resolved_at)

    def test_admin_delete_target_resolves_report_even_if_target_missing(self):
        post_content_type = ContentType.objects.get_for_model(Post)
        comment_content_type = ContentType.objects.get_for_model(Comment)
        post_report = Report.objects.create(
            reporter=self.user,
            content_type=post_content_type,
            object_id=self.post.id,
            reason=Report.REASON_SPAM,
        )
        comment_report = Report.objects.create(
            reporter=self.user,
            content_type=comment_content_type,
            object_id=self.comment.id,
            reason=Report.REASON_ABUSE,
        )
        self.client.force_authenticate(self.admin)

        delete_post_response = self.client.post(
            reverse("admin-actions"),
            {"action": "delete_target", "report_id": post_report.id},
            format="json",
        )
        self.assertEqual(delete_post_response.status_code, status.HTTP_200_OK)
        self.assertFalse(Post.objects.filter(pk=self.post.id).exists())
        post_report.refresh_from_db()
        self.assertEqual(post_report.status, Report.STATUS_RESOLVED)
        self.assertIsNotNone(post_report.resolved_at)

        self.comment.delete()
        delete_missing_response = self.client.post(
            reverse("admin-actions"),
            {"action": "delete_target", "report_id": comment_report.id},
            format="json",
        )
        self.assertEqual(delete_missing_response.status_code, status.HTTP_200_OK)
        comment_report.refresh_from_db()
        self.assertEqual(comment_report.status, Report.STATUS_RESOLVED)
        self.assertIsNotNone(comment_report.resolved_at)

    def test_admin_suspend_user_deactivates_author_and_resolves_report(self):
        content_type = ContentType.objects.get_for_model(Comment)
        report = Report.objects.create(
            reporter=self.user,
            content_type=content_type,
            object_id=self.comment.id,
            reason=Report.REASON_ABUSE,
        )
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            reverse("admin-actions"),
            {
                "action": "suspend_user",
                "report_id": report.id,
                "suspend_days": 7,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.author.refresh_from_db()
        report.refresh_from_db()
        self.assertFalse(self.author.is_active)
        self.assertEqual(report.status, Report.STATUS_RESOLVED)

    def test_suspend_user_on_staff_or_superuser_returns_400(self):
        staff_author = User.objects.create_user(
            username="staff_author",
            password="testpass123",
            is_staff=True,
        )
        staff_post = Post.objects.create(
            subject=self.subject,
            author=staff_author,
            title="Staff post",
            body="Staff content.",
        )
        content_type = ContentType.objects.get_for_model(Post)
        report = Report.objects.create(
            reporter=self.user,
            content_type=content_type,
            object_id=staff_post.id,
            reason=Report.REASON_ABUSE,
        )
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            reverse("admin-actions"),
            {
                "action": "suspend_user",
                "report_id": report.id,
                "suspend_days": 2,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        staff_author.refresh_from_db()
        report.refresh_from_db()
        self.assertTrue(staff_author.is_active)
        self.assertEqual(report.status, Report.STATUS_OPEN)
