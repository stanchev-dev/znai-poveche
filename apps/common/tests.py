from io import StringIO
from types import SimpleNamespace

from django.core.management import call_command
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import Profile
from apps.common.utils.pagination import build_olx_page_items
from apps.discussions.models import Comment, Post, Subject


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


class PaginationUtilsTests(TestCase):
    def test_single_page_returns_only_one(self):
        paginator = SimpleNamespace(num_pages=1)
        page_obj = SimpleNamespace(number=1)

        self.assertEqual(build_olx_page_items(paginator, page_obj), [1])

    def test_small_page_count_returns_all_pages(self):
        paginator = SimpleNamespace(num_pages=5)
        page_obj = SimpleNamespace(number=3)

        self.assertEqual(build_olx_page_items(paginator, page_obj), [1, 2, 3, 4, 5])

    def test_large_page_count_returns_olx_like_middle_window(self):
        paginator = SimpleNamespace(num_pages=25)
        page_obj = SimpleNamespace(number=10)

        self.assertEqual(
            build_olx_page_items(paginator, page_obj),
            [1, '…', 9, 10, 11, '…', 25],
        )


class LeaderboardPageScopeTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user_one = self.user_model.objects.create_user(username="ivan")
        self.user_two = self.user_model.objects.create_user(username="maria")

        profile_one, _ = Profile.objects.get_or_create(user=self.user_one)
        profile_one.reputation_points = 40
        profile_one.save(update_fields=["reputation_points"])

        profile_two, _ = Profile.objects.get_or_create(user=self.user_two)
        profile_two.reputation_points = 30
        profile_two.save(update_fields=["reputation_points"])

        self.subject_math = Subject.objects.create(name="Математика")
        self.subject_history = Subject.objects.create(name="История")

        post = Post.objects.create(
            subject=self.subject_math,
            author=self.user_two,
            title="Тест",
            body="Тяло",
            score=18,
        )
        Comment.objects.create(
            post=post,
            author=self.user_two,
            body="Коментар",
            score=7,
        )

    def test_global_scope_selected_by_default(self):
        response = self.client.get(reverse("leaderboard-page"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["scope"], "global")

    def test_subject_scope_filters_by_selected_subject(self):
        response = self.client.get(
            reverse("leaderboard-page"),
            {"scope": "subject", "subject": self.subject_math.slug},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["scope"], "subject")
        self.assertEqual(response.context["selected_subject"], self.subject_math)
        rows = response.context["leaderboard_rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["username"], "maria")
        self.assertEqual(rows[0]["points"], 25)


    def test_subject_scope_with_no_participants_hides_podium_and_shows_empty_state(self):
        response = self.client.get(
            reverse("leaderboard-page"),
            {"scope": "subject", "subject": self.subject_history.slug},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["top_three"], [])
        self.assertContains(response, "Все още няма участници в класацията.")
        self.assertNotContains(response, 'class="lb-hero rounded-4 p-3 p-md-4"')

    def test_subject_scope_without_subject_falls_back_to_global(self):
        response = self.client.get(reverse("leaderboard-page"), {"scope": "subject"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["scope"], "global")
        self.assertIsNone(response.context["selected_subject"])
