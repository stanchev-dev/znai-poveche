from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.discussions.models import Subject


class WebPageSmokeTests(TestCase):
    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_marketplace_page(self):
        response = self.client.get('/marketplace/')
        self.assertEqual(response.status_code, 200)

    def test_leaderboard_page(self):
        response = self.client.get('/leaderboard/')
        self.assertEqual(response.status_code, 200)

    def test_subject_page(self):
        response = self.client.get('/subjects/anything/')
        self.assertEqual(response.status_code, 200)

    def test_post_page(self):
        response = self.client.get('/posts/99999/')
        self.assertEqual(response.status_code, 200)

    def test_marketplace_detail_page(self):
        response = self.client.get('/marketplace/99999/')
        self.assertEqual(response.status_code, 200)


class SeedCommandTests(TestCase):
    def test_seed_command_runs(self):
        out = StringIO()
        call_command('seed', stdout=out)
        output = out.getvalue()
        self.assertIn('Seed completed.', output)
        self.assertTrue(Subject.objects.exists())
