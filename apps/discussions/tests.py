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

    def test_post_create_updates_max_level_reached(self):
        profile = Profile.objects.get(user=self.user)
        profile.reputation_points = 24
        profile.max_level_reached = 1
        profile.daily_base_points = 0
        profile.daily_base_points_date = timezone.localdate()
        profile.save()

        response = self.client.post(
            reverse("api-posts-list"),
            {
                "subject": self.subject.slug,
                "title": "Level up post",
                "body": "Short body",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        profile.refresh_from_db()
        self.assertEqual(profile.reputation_points, 26)
        self.assertEqual(profile.max_level_reached, 2)

    def test_post_create_updates_max_level_reached_multiple_levels(self):
        profile = Profile.objects.get(user=self.user)
        profile.reputation_points = 49
        profile.max_level_reached = 2
        profile.daily_base_points = 0
        profile.daily_base_points_date = timezone.localdate()
        profile.save()

        response = self.client.post(
            reverse("api-posts-list"),
            {
                "subject": self.subject.slug,
                "title": "Second level up post",
                "body": "Short body",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        profile.refresh_from_db()
        self.assertEqual(profile.reputation_points, 51)
        self.assertEqual(profile.max_level_reached, 3)

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


class LeaderboardTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.subject_one = Subject.objects.create(name="Subject One")
        self.subject_two = Subject.objects.create(name="Subject Two")
        self.user_one = User.objects.create_user(
            username="user_one",
            password="testpass123",
        )
        self.user_two = User.objects.create_user(
            username="user_two",
            password="testpass123",
        )
        self.user_three = User.objects.create_user(
            username="user_three",
            password="testpass123",
        )
        self.user_four = User.objects.create_user(
            username="user_four",
            password="testpass123",
        )

    def test_global_leaderboard_orders_by_reputation_and_id(self):
        Profile.objects.filter(user=self.user_one).update(
            reputation_points=40
        )
        Profile.objects.filter(user=self.user_two).update(
            reputation_points=90
        )
        Profile.objects.filter(user=self.user_three).update(
            reputation_points=90
        )

        response = self.client.get(reverse("leaderboard"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(results[0]["user_id"], self.user_two.id)
        self.assertEqual(results[1]["user_id"], self.user_three.id)
        self.assertEqual(results[2]["user_id"], self.user_one.id)
        self.assertIsNone(results[0]["subject_score"])

    def test_subject_leaderboard_scores_and_order(self):
        post_one = Post.objects.create(
            subject=self.subject_one,
            author=self.user_one,
            title="Post One",
            body="Body",
            score=2,
        )
        Post.objects.create(
            subject=self.subject_one,
            author=self.user_one,
            title="Post Two",
            body="Body",
            score=4,
        )
        post_two = Post.objects.create(
            subject=self.subject_one,
            author=self.user_two,
            title="Post Three",
            body="Body",
            score=5,
        )
        subject_two_post = Post.objects.create(
            subject=self.subject_two,
            author=self.user_two,
            title="Other Subject Post",
            body="Body",
            score=10,
        )

        Comment.objects.create(
            post=post_one,
            author=self.user_one,
            body="Comment",
            score=3,
        )
        Comment.objects.create(
            post=post_two,
            author=self.user_two,
            body="Comment",
            score=1,
        )
        Comment.objects.create(
            post=post_one,
            author=self.user_three,
            body="Comment",
            score=2,
        )
        Comment.objects.create(
            post=post_one,
            author=self.user_three,
            body="Other comment",
            score=0,
        )
        Comment.objects.create(
            post=subject_two_post,
            author=self.user_two,
            body="Subject two comment",
            score=4,
        )
        Comment.objects.create(
            post=Post.objects.create(
                subject=self.subject_two,
                author=self.user_one,
                title="Subject Two Post",
                body="Body",
                score=7,
            ),
            author=self.user_one,
            body="Subject two comment",
            score=5,
        )

        response = self.client.get(
            reverse("leaderboard"),
            {"scope": "subject", "subject": self.subject_one.slug},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(results[0]["user_id"], self.user_one.id)
        self.assertEqual(results[0]["subject_score"], 9)
        self.assertEqual(results[1]["user_id"], self.user_two.id)
        self.assertEqual(results[1]["subject_score"], 6)
        self.assertEqual(results[2]["user_id"], self.user_three.id)
        self.assertEqual(results[2]["subject_score"], 2)
        self.assertNotIn(self.user_four.id, [item["user_id"] for item in results])

    def test_subject_scope_requires_subject(self):
        response = self.client.get(reverse("leaderboard"), {"scope": "subject"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_scope_returns_400(self):
        response = self.client.get(reverse("leaderboard"), {"scope": "other"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subject_not_found_returns_404(self):
        response = self.client.get(
            reverse("leaderboard"),
            {"scope": "subject", "subject": "missing"},
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
