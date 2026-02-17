from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .admin import TeacherVerificationRequestAdmin
from .models import Profile, TeacherVerificationRequest


class ProfileSignalTests(TestCase):
    def test_profile_created_for_new_user(self):
        User = get_user_model()
        user = User.objects.create_user(username="newuser", password="testpass123")

        self.assertTrue(Profile.objects.filter(user=user).exists())


class TeacherVerificationViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="teacher", email="teacher@example.com", password="testpass123"
        )
        self.url = reverse("teacher-verify")

    def test_get_verification_page_requires_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_post_with_no_proof_fields_returns_validation_error(self):
        self.client.login(username="teacher", password="testpass123")

        response = self.client.post(self.url, data={"subjects": "математика"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Моля, добави поне един начин за доказателство: имейл, линк или документ.",
        )
        self.assertEqual(TeacherVerificationRequest.objects.count(), 0)

    def test_post_with_school_email_creates_pending_request(self):
        self.client.login(username="teacher", password="testpass123")

        response = self.client.post(
            self.url,
            data={
                "subjects": "математика, физика",
                "school_email": "ime.familiya@school.bg",
            },
        )

        self.assertEqual(response.status_code, 302)
        request_obj = TeacherVerificationRequest.objects.get(user=self.user)
        self.assertEqual(request_obj.status, TeacherVerificationRequest.Status.PENDING)


class TeacherVerificationAdminTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="teacher2", email="teacher2@example.com", password="testpass123"
        )
        self.request_obj = TeacherVerificationRequest.objects.create(
            user=self.user,
            school_email="teacher2@school.bg",
            status=TeacherVerificationRequest.Status.PENDING,
        )
        self.admin = TeacherVerificationRequestAdmin(
            TeacherVerificationRequest, AdminSite()
        )

    def test_admin_approve_sets_verified_teacher_and_approved_status(self):
        self.admin.approve_requests(None, TeacherVerificationRequest.objects.filter(pk=self.request_obj.pk))

        self.request_obj.refresh_from_db()
        self.user.profile.refresh_from_db()

        self.assertEqual(self.request_obj.status, TeacherVerificationRequest.Status.APPROVED)
        self.assertIsNotNone(self.request_obj.decided_at)
        self.assertTrue(self.user.profile.is_verified_teacher)
