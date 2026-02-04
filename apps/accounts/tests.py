from django.contrib.auth import get_user_model
from django.test import TestCase


class ProfileSignalTests(TestCase):
    def test_profile_created_for_new_user(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username="newuser", password="testpass123")

        self.assertIsNotNone(user.profile)
