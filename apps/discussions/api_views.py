from django.db import transaction
from django.db.models import (
    ExpressionWrapper,
    F,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Profile

from .models import Comment, CommentVote, Post, PostVote, Subject
from .serializers import (
    CommentCreateSerializer,
    CommentSerializer,
    PostBodyUpdateSerializer,
    PostCreateSerializer,
    PostDetailSerializer,
    PostListSerializer,
    SubjectSerializer,
    VoteInputSerializer,
)
from .throttles import CommentCreateThrottle, PostCreateThrottle


class PostPagination(PageNumberPagination):
    page_size = 10


class LeaderboardPagination(PageNumberPagination):
    page_size = 20

    def get_paginated_response(self, data):
        return Response(
            {
                "scope": getattr(self, "scope", None),
                "subject": getattr(self, "subject", None),
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )


def apply_base_points(profile: Profile, points_to_add: int) -> None:
    today = timezone.localdate()
    update_fields = []
    if profile.daily_base_points_date != today:
        profile.daily_base_points = 0
        profile.daily_base_points_date = today
        update_fields.extend(["daily_base_points", "daily_base_points_date"])

    remaining_cap = max(0, 30 - profile.daily_base_points)
    if points_to_add > remaining_cap:
        points_to_add = remaining_cap

    if points_to_add > 0:
        profile.daily_base_points += points_to_add
        profile.reputation_points += points_to_add
        update_fields.extend(["daily_base_points", "reputation_points"])
        new_level = calculate_level(profile.reputation_points)
        if new_level > profile.max_level_reached:
            profile.max_level_reached = new_level
            update_fields.append("max_level_reached")

    if update_fields:
        profile.save(update_fields=update_fields)


class SubjectListView(ListAPIView):
    queryset = Subject.objects.order_by("sort_order", "name")
    serializer_class = SubjectSerializer


class PostListView(ListCreateAPIView):
    serializer_class = PostListSerializer
    pagination_class = PostPagination
    queryset = (
        Post.objects.select_related("subject", "author", "author__profile").all()
    )

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return []

    def get_throttles(self):
        if self.request.method == "POST":
            return [PostCreateThrottle()]
        return []

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PostCreateSerializer
        return PostListSerializer

    def get_queryset(self):
        queryset = self.queryset
        subject_slug = self.request.query_params.get("subject")
        if subject_slug and subject_slug != "all":
            queryset = queryset.filter(subject__slug=subject_slug)

        search_text = self.request.query_params.get("q")
        if search_text:
            queryset = queryset.filter(
                Q(title__icontains=search_text) | Q(body__icontains=search_text)
            )

        sort = self.request.query_params.get("sort", "new")
        if sort == "top":
            queryset = queryset.order_by("-score", "-created_at")
        else:
            queryset = queryset.order_by("-created_at")

        return queryset

    def perform_create(self, serializer):
        points_to_add = 2
        with transaction.atomic():
            profile = Profile.objects.select_for_update().get(
                user=self.request.user
            )
            apply_base_points(profile, points_to_add)
            serializer.save(author=self.request.user)


class PostCreateAPIView(PostListView):
    http_method_names = ["post"]
    permission_classes = [IsAuthenticated]
    throttle_classes = [PostCreateThrottle]
    serializer_class = PostCreateSerializer

    def get_queryset(self):
        return Post.objects.none()


class PostDetailView(RetrieveAPIView):
    serializer_class = PostDetailSerializer

    def get_queryset(self):
        queryset = Post.objects.select_related(
            "subject",
            "author",
            "author__profile",
        )
        user = self.request.user
        if not user.is_authenticated:
            return queryset.annotate(user_vote=Value(0, output_field=IntegerField()))

        vote_subquery = PostVote.objects.filter(
            post=OuterRef("pk"),
            voter=user,
        ).values("value")[:1]
        return queryset.annotate(
            user_vote=Coalesce(
                Subquery(vote_subquery, output_field=IntegerField()),
                Value(0, output_field=IntegerField()),
            )
        )


class PostCommentListView(ListCreateAPIView):
    serializer_class = CommentSerializer
    queryset = Comment.objects.select_related("author", "author__profile").all()

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return []

    def get_throttles(self):
        if self.request.method == "POST":
            return [CommentCreateThrottle()]
        return []

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(post_id=self.kwargs["post_id"]).all()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.annotate(user_vote=Value(0, output_field=IntegerField()))

        vote_subquery = CommentVote.objects.filter(
            comment=OuterRef("pk"),
            voter=user,
        ).values("value")[:1]
        return queryset.annotate(
            user_vote=Coalesce(
                Subquery(vote_subquery, output_field=IntegerField()),
                Value(0, output_field=IntegerField()),
            )
        )

    def perform_create(self, serializer):
        points_to_add = 1
        with transaction.atomic():
            post = get_object_or_404(Post, pk=self.kwargs["post_id"])
            profile = Profile.objects.select_for_update().get(
                user=self.request.user
            )
            apply_base_points(profile, points_to_add)
            serializer.save(
                author=self.request.user,
                post=post,
            )


class CommentCreateAPIView(PostCommentListView):
    http_method_names = ["post"]
    permission_classes = [IsAuthenticated]
    throttle_classes = [CommentCreateThrottle]
    serializer_class = CommentCreateSerializer

    def get_queryset(self):
        return Comment.objects.none()


def calculate_level(points: int) -> int:
    return max(1, (points // 25) + 1)


def apply_reputation_delta(profile: Profile, reputation_delta: int) -> None:
    profile.reputation_points = max(
        0,
        profile.reputation_points + reputation_delta,
    )
    new_level = calculate_level(profile.reputation_points)
    if new_level > profile.max_level_reached:
        profile.max_level_reached = new_level


def compute_score_delta(prev_vote: int, next_vote: int) -> int:
    return next_vote - prev_vote


def rep_value(vote: int) -> int:
    return 1 if vote == 1 else 0


class BaseVoteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = []
    serializer_class = VoteInputSerializer
    target_model = None
    vote_model = None
    target_field = ""

    def allow_negative_score(self) -> bool:
        return True

    def compute_reputation_delta(self, prev_vote: int, next_vote: int) -> int:
        return rep_value(next_vote) - rep_value(prev_vote)

    def post(self, request, pk):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        vote_value = int(serializer.validated_data["value"])

        with transaction.atomic():
            target = get_object_or_404(
                self.target_model.objects.select_for_update(),
                pk=pk,
            )

            if target.author_id == request.user.id:
                return Response(
                    {"detail": "Self-voting is not allowed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            vote_lookup = {
                "voter": request.user,
                self.target_field: target,
            }
            vote = (
                self.vote_model.objects.select_for_update()
                .filter(**vote_lookup)
                .first()
            )
            prev_vote = vote.value if vote else 0
            next_vote = 0 if prev_vote == vote_value else vote_value

            if (
                not self.allow_negative_score()
                and target.score <= 0
                and next_vote == -1
            ):
                author_profile = Profile.objects.select_for_update().get(
                    user=target.author
                )
                if vote and vote.value == -1:
                    vote.delete()

                return Response(
                    {
                        "score": target.score,
                        "user_vote": 0,
                        "author_points": author_profile.reputation_points,
                        "author_level": author_profile.level,
                    },
                    status=status.HTTP_200_OK,
                )

            score_delta = compute_score_delta(prev_vote, next_vote)
            reputation_delta = self.compute_reputation_delta(
                prev_vote,
                next_vote,
            )

            if (
                not self.allow_negative_score()
                and target.score == 0
                and prev_vote == -1
                and next_vote == 0
            ):
                score_delta = 0
                reputation_delta = 0

            if (
                not self.allow_negative_score()
                and target.score == 0
                and prev_vote == -1
                and next_vote == 1
            ):
                score_delta = 1

            if score_delta != 0:
                if not self.allow_negative_score():
                    target.score = max(0, target.score + score_delta)
                else:
                    target.score += score_delta
                target.save(update_fields=["score"])

            author_profile = Profile.objects.select_for_update().get(
                user=target.author
            )
            should_apply_reputation = reputation_delta != 0
            if should_apply_reputation:
                apply_reputation_delta(author_profile, reputation_delta)
                author_profile.save(
                    update_fields=["reputation_points", "max_level_reached"]
                )

            if next_vote == 0:
                if vote:
                    vote.delete()
            elif vote is None:
                self.vote_model.objects.create(**vote_lookup, value=next_vote)
            else:
                vote.value = next_vote
                vote.save(update_fields=["value"])

            return Response(
                {
                    "score": target.score,
                    "user_vote": next_vote,
                    "author_points": author_profile.reputation_points,
                    "author_level": author_profile.level,
                },
                status=status.HTTP_200_OK,
            )


class PostVoteAPIView(BaseVoteAPIView):
    target_model = Post
    vote_model = PostVote
    target_field = "post"

    def allow_negative_score(self) -> bool:
        return False

class CommentVoteAPIView(BaseVoteAPIView):
    target_model = Comment
    vote_model = CommentVote
    target_field = "comment"


class LeaderboardAPIView(APIView):
    permission_classes = [AllowAny]
    pagination_class = LeaderboardPagination

    def get(self, request):
        scope = request.query_params.get("scope", "global")
        if scope not in {"global", "subject"}:
            return Response(
                {"detail": "Invalid scope."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subject = None
        if scope == "subject":
            subject_slug = request.query_params.get("subject")
            if not subject_slug:
                return Response(
                    {"detail": "Subject is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subject = get_object_or_404(Subject, slug=subject_slug)
            queryset = self._get_subject_queryset(subject)
        else:
            queryset = Profile.objects.select_related("user").order_by(
                "-reputation_points",
                "user_id",
            )

        paginator = self.pagination_class()
        paginator.scope = scope
        paginator.subject = (
            SubjectSerializer(subject).data if subject is not None else None
        )
        page = paginator.paginate_queryset(queryset, request, view=self)
        results = self._build_results(
            page,
            paginator,
            request,
            scope=scope,
        )
        return paginator.get_paginated_response(results)

    def _get_subject_queryset(self, subject: Subject):
        post_score_subquery = (
            Post.objects.filter(
                author_id=OuterRef("user_id"),
                subject=subject,
            )
            .values("author_id")
            .annotate(total_score=Sum("score"))
            .values("total_score")
        )
        comment_score_subquery = (
            Comment.objects.filter(
                author_id=OuterRef("user_id"),
                post__subject=subject,
            )
            .values("author_id")
            .annotate(total_score=Sum("score"))
            .values("total_score")
        )

        queryset = Profile.objects.select_related("user").annotate(
            post_score=Coalesce(
                Subquery(post_score_subquery, output_field=IntegerField()),
                0,
            ),
            comment_score=Coalesce(
                Subquery(comment_score_subquery, output_field=IntegerField()),
                0,
            ),
        )
        queryset = queryset.annotate(
            subject_score=ExpressionWrapper(
                F("post_score") + F("comment_score"),
                output_field=IntegerField(),
            )
        ).filter(subject_score__gt=0)
        return queryset.order_by("-subject_score", "user_id")

    def _build_results(
        self,
        page,
        paginator: LeaderboardPagination,
        request,
        *,
        scope: str,
    ):
        if page is None:
            return []
        page_number = paginator.page.number
        page_size = paginator.get_page_size(request) or len(page)
        offset = (page_number - 1) * page_size
        results = []
        for index, profile in enumerate(page):
            results.append(
                {
                    "rank": offset + index + 1,
                    "user_id": profile.user_id,
                    "username": profile.user.get_username(),
                    "display_name": profile.display_name,
                    "level": profile.level,
                    "reputation_points": profile.reputation_points,
                    "subject_score": (
                        int(profile.subject_score)
                        if scope == "subject"
                        else None
                    ),
                }
            )
        return results


class MyPostBodyUpdateAPIView(UpdateAPIView):
    serializer_class = PostBodyUpdateSerializer
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.select_related("author")

    def get_queryset(self):
        return self.queryset.filter(author=self.request.user)


class MyPostDeleteAPIView(DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.select_related("author")

    def get_queryset(self):
        return self.queryset.filter(author=self.request.user)


class MyCommentDeleteAPIView(DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.select_related("author")

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return self.queryset
        return self.queryset.filter(author=user)
