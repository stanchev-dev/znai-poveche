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

    def test_legal_and_info_pages_use_accordion_layout(self):
        for path, title in [
            ('/privacy/', 'Политика за поверителност'),
            ('/terms/', 'Общи условия'),
            ('/mission/', 'Нашата мисия'),
        ]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                content = response.content.decode()
                self.assertIn(f'<h1 class="mb-4">{title}</h1>', content)
                self.assertIn('class="accordion" id="infoAccordion"', content)
                self.assertIn('accordion-collapse collapse show', content)
                self.assertNotIn('Съдържание', content)


class SeedCommandTests(TestCase):
    def test_seed_command_runs(self):
        out = StringIO()
        call_command('seed', stdout=out)
        output = out.getvalue()
        self.assertIn('Seed completed.', output)
        self.assertTrue(Subject.objects.exists())
