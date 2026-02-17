from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Profile


class ProfileSignalTests(TestCase):
    def test_profile_created_for_new_user(self):
        User = get_user_model()
        user = User.objects.create_user(username="newuser", password="testpass123")

        self.assertTrue(Profile.objects.filter(user=user).exists())


class RegistrationRoleTests(TestCase):
    def test_registration_saves_teacher_role_on_profile(self):
        response = self.client.post(
            reverse("register"),
            data={
                "username": "newteacher",
                "display_name": "Нов Учител",
                "role": Profile.Role.TEACHER,
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            },
        )

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username="newteacher")
        self.assertEqual(user.profile.role, Profile.Role.TEACHER)
        self.assertEqual(user.profile.display_name, "Нов Учител")

    def test_registration_defaults_to_learner_role(self):
        user = get_user_model().objects.create_user(
            username="defaultrole",
            password="testpass123",
        )

        self.assertEqual(user.profile.role, Profile.Role.LEARNER)
