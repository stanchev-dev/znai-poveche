from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Profile

class ProfileSignalTests(TestCase):
    def test_profile_created_for_new_user(self):
        User = get_user_model()
        user = User.objects.create_user(username="newuser", password="testpass123")

        self.assertTrue(Profile.objects.filter(user=user).exists())
