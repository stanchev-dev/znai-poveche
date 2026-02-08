from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Profile
from apps.discussions.models import Comment, Post, Subject


User = get_user_model()


class PostCreatePointsTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="author",
            password="testpass123",
        )
        self.subject = Subject.objects.create(name="General")
        self.client.force_authenticate(self.user)

    def test_post_create_awards_points(self):
        response = self.client.post(
            reverse("api-posts-list"),
            {
                "subject": self.subject.slug,
                "title": "A post title",
                "body": "Short body",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.reputation_points, 2)
        self.assertEqual(profile.daily_base_points, 2)

    def test_daily_cap_prevents_extra_points(self):
        profile = Profile.objects.get(user=self.user)
        profile.daily_base_points = 30
        profile.daily_base_points_date = timezone.localdate()
        profile.reputation_points = 30
        profile.save()

        response = self.client.post(
            reverse("api-posts-list"),
            {
                "subject": self.subject.slug,
                "title": "Another post title",
                "body": "Short body",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        profile.refresh_from_db()
        self.assertEqual(profile.reputation_points, 30)
        self.assertEqual(profile.daily_base_points, 30)

    def test_post_create_throttle(self):
        payload = {
            "subject": self.subject.slug,
            "title": "A post title",
            "body": "Short body",
        }
        for _ in range(3):
            response = self.client.post(
                reverse("api-posts-list"),
                payload,
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            reverse("api-posts-list"),
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_post_create_rejects_whitespace_title_or_body(self):
        response = self.client.post(
            reverse("api-posts-list"),
            {
                "subject": self.subject.slug,
                "title": "   ",
                "body": "Valid body",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            reverse("api-posts-list"),
            {
                "subject": self.subject.slug,
                "title": "Valid title",
                "body": "   ",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CommentCreatePointsTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="commenter",
            password="testpass123",
        )
        self.subject = Subject.objects.create(name="Announcements")
        self.post = Post.objects.create(
            subject=self.subject,
            author=self.user,
            title="Seed Post",
            body="This body has more than thirty characters.",
        )
        self.client.force_authenticate(self.user)

    def test_comment_create_awards_points(self):
        response = self.client.post(
            reverse("api-posts-comments", kwargs={"post_id": self.post.id}),
            {"body": "Ok"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.reputation_points, 1)
        self.assertEqual(profile.daily_base_points, 1)

    def test_comment_create_throttle(self):
        for _ in range(10):
            response = self.client.post(
                reverse(
                    "api-posts-comments", kwargs={"post_id": self.post.id}
                ),
                {"body": "Ok"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            reverse("api-posts-comments", kwargs={"post_id": self.post.id}),
            {"body": "Ok"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_comment_create_rejects_whitespace_body(self):
        response = self.client.post(
            reverse("api-posts-comments", kwargs={"post_id": self.post.id}),
            {"body": "   "},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class VoteTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.author = User.objects.create_user(
            username="author",
            password="testpass123",
        )
        self.voter = User.objects.create_user(
            username="voter",
            password="testpass123",
        )
        self.subject = Subject.objects.create(name="Voting")
        self.post = Post.objects.create(
            subject=self.subject,
            author=self.author,
            title="Vote Post",
            body="Vote body content.",
        )
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.author,
            body="Vote comment",
        )
        self.client.force_authenticate(self.voter)

    def test_post_upvote_awards_score_and_points(self):
        response = self.client.post(
            reverse("api-posts-vote", kwargs={"pk": self.post.id}),
            {"value": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        author_profile = Profile.objects.get(user=self.author)
        self.assertEqual(self.post.score, 1)
        self.assertEqual(author_profile.reputation_points, 2)

    def test_post_downvote_awards_score_and_points(self):
        response = self.client.post(
            reverse("api-posts-vote", kwargs={"pk": self.post.id}),
            {"value": -1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        author_profile = Profile.objects.get(user=self.author)
        self.assertEqual(self.post.score, -1)
        self.assertEqual(author_profile.reputation_points, 0)

    def test_switch_upvote_to_downvote(self):
        self.client.post(
            reverse("api-posts-vote", kwargs={"pk": self.post.id}),
            {"value": 1},
            format="json",
        )

        response = self.client.post(
            reverse("api-posts-vote", kwargs={"pk": self.post.id}),
            {"value": -1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        author_profile = Profile.objects.get(user=self.author)
        self.assertEqual(self.post.score, -1)
        self.assertEqual(author_profile.reputation_points, 0)

    def test_switch_downvote_to_upvote(self):
        self.client.post(
            reverse("api-posts-vote", kwargs={"pk": self.post.id}),
            {"value": -1},
            format="json",
        )

        response = self.client.post(
            reverse("api-posts-vote", kwargs={"pk": self.post.id}),
            {"value": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        author_profile = Profile.objects.get(user=self.author)
        self.assertEqual(self.post.score, 1)
        self.assertEqual(author_profile.reputation_points, 2)

    def test_repeat_vote_is_idempotent(self):
        self.client.post(
            reverse("api-posts-vote", kwargs={"pk": self.post.id}),
            {"value": 1},
            format="json",
        )
        author_profile = Profile.objects.get(user=self.author)
        author_profile.reputation_points = 5
        author_profile.save()

        response = self.client.post(
            reverse("api-posts-vote", kwargs={"pk": self.post.id}),
            {"value": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        author_profile.refresh_from_db()
        self.assertEqual(self.post.score, 1)
        self.assertEqual(author_profile.reputation_points, 5)

    def test_self_vote_rejected(self):
        self.client.force_authenticate(self.author)
        response = self.client.post(
            reverse("api-posts-vote", kwargs={"pk": self.post.id}),
            {"value": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.post.refresh_from_db()
        author_profile = Profile.objects.get(user=self.author)
        self.assertEqual(self.post.score, 0)
        self.assertEqual(author_profile.reputation_points, 0)

    def test_invalid_value_rejected(self):
        response = self.client.post(
            reverse("api-posts-vote", kwargs={"pk": self.post.id}),
            {"value": 2},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            reverse("api-posts-vote", kwargs={"pk": self.post.id}),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reputation_clamps_on_downvote_floor(self):
        profile = Profile.objects.get(user=self.author)
        profile.reputation_points = 25
        profile.max_level_reached = 2
        profile.save()

        response = self.client.post(
            reverse("api-comments-vote", kwargs={"pk": self.comment.id}),
            {"value": -1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.score, -1)
        self.assertEqual(profile.reputation_points, 25)

    def test_vote_throttle(self):
        for _ in range(50):
            response = self.client.post(
                reverse("api-posts-vote", kwargs={"pk": self.post.id}),
                {"value": 1},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            reverse("api-posts-vote", kwargs={"pk": self.post.id}),
            {"value": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_vote_does_not_change_daily_base_points(self):
        profile = Profile.objects.get(user=self.author)
        profile.daily_base_points = 10
        profile.save()

        response = self.client.post(
            reverse("api-posts-vote", kwargs={"pk": self.post.id}),
            {"value": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        self.assertEqual(profile.daily_base_points, 10)
