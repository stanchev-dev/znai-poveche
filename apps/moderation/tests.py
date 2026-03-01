from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.discussions.models import Comment, Post, Subject
from apps.marketplace.models import Listing

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
        self.listing = Listing.objects.create(
            subject=self.subject,
            owner=self.author,
            price_per_hour="25.00",
            description="Listing for moderation tests.",
            contact_phone="0888123456",
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
                "target_type": "invalid",
                "target_id": 1,
                "reason": Report.REASON_OTHER,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_user_can_report_listing(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("report-create"),
            {
                "target_type": "listing",
                "target_id": self.listing.id,
                "reason": Report.REASON_SPAM,
                "message": "Подозрителна обява.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["target_type"], "listing")
        self.assertEqual(response.data["target_id"], self.listing.id)

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


class ModerationAdminTests(TestCase):
    def setUp(self):
        self.client = self.client_class()
        self.admin = User.objects.create_user(
            username="admin",
            password="testpass123",
            is_staff=True,
            is_superuser=True,
        )
        self.reporter = User.objects.create_user(
            username="reporter_admin",
            password="testpass123",
            email="reporter@example.com",
        )
        self.author = User.objects.create_user(
            username="author_admin",
            password="testpass123",
        )
        self.subject = Subject.objects.create(name="Admin moderation")
        self.post = Post.objects.create(
            subject=self.subject,
            author=self.author,
            title="Post for admin report",
            body="Body",
        )
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.author,
            body="Comment for admin report",
        )
        self.listing = Listing.objects.create(
            subject=self.subject,
            owner=self.author,
            price_per_hour="30.00",
            description="Listing for admin report",
            contact_phone="0888123456",
        )

    def _make_report_for(self, model, object_id, reason=Report.REASON_SPAM):
        return Report.objects.create(
            reporter=self.reporter,
            content_type=ContentType.objects.get_for_model(model),
            object_id=object_id,
            reason=reason,
        )

    def test_admin_reports_changelist_is_accessible(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin:moderation_report_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reports")

    def test_delete_target_content_action_handles_post_comment_and_missing_target(self):
        post_report = self._make_report_for(Post, self.post.id)
        comment_report = self._make_report_for(
            Comment,
            self.comment.id,
            reason=Report.REASON_ABUSE,
        )
        missing_report = self._make_report_for(Comment, 999999, reason=Report.REASON_OTHER)

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin:moderation_report_changelist"),
            {
                "action": "delete_target_content",
                "_selected_action": [post_report.id, comment_report.id, missing_report.id],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())
        post_report.refresh_from_db()
        comment_report.refresh_from_db()
        missing_report.refresh_from_db()
        self.assertEqual(post_report.status, Report.STATUS_RESOLVED)
        self.assertEqual(comment_report.status, Report.STATUS_RESOLVED)
        self.assertEqual(missing_report.status, Report.STATUS_OPEN)


    def test_delete_target_content_action_supports_listing(self):
        listing_report = self._make_report_for(Listing, self.listing.id, reason=Report.REASON_OTHER)

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin:moderation_report_changelist"),
            {
                "action": "delete_target_content",
                "_selected_action": [listing_report.id],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Listing.objects.filter(id=self.listing.id).exists())
        listing_report.refresh_from_db()
        self.assertEqual(listing_report.status, Report.STATUS_RESOLVED)



    def test_mark_as_resolved_action(self):
        report = self._make_report_for(Comment, self.comment.id)
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("admin:moderation_report_changelist"),
            {
                "action": "mark_as_resolved",
                "_selected_action": [report.id],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        self.assertEqual(report.status, Report.STATUS_RESOLVED)
        self.assertIsNotNone(report.resolved_at)

    def test_changelist_shows_listing_report(self):
        listing_report = self._make_report_for(Listing, self.listing.id)
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin:moderation_report_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"listing #{self.listing.id}")
        self.assertContains(response, str(listing_report.id))

    def test_target_type_filter_options_are_bulgarian(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin:moderation_report_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Коментари")
        self.assertContains(response, "Дискусии")
        self.assertContains(response, "Обяви")


