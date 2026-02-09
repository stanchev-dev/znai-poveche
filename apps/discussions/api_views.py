from django.db import IntegrityError, transaction
from django.db.models import (
    ExpressionWrapper,
    F,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Sum,
)
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Profile

from .models import Comment, CommentVote, Post, PostVote, Subject
from .serializers import (
    CommentCreateSerializer,
    CommentSerializer,
    PostCreateSerializer,
    PostDetailSerializer,
    PostListSerializer,
    SubjectSerializer,
    VoteInputSerializer,
)
from .throttles import CommentCreateThrottle, PostCreateThrottle, VoteThrottle


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
    queryset = Subject.objects.all()
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
    queryset = Post.objects.select_related(
        "subject",
        "author",
        "author__profile",
    )
    serializer_class = PostDetailSerializer


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
        return self.queryset.filter(post_id=self.kwargs["post_id"]).all()

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
    return (points // 25) + 1


def apply_reputation_delta(profile: Profile, reputation_delta: int) -> None:
    current_level = calculate_level(profile.reputation_points)
    if profile.max_level_reached < current_level:
        profile.max_level_reached = current_level

    profile.reputation_points += reputation_delta

    new_level = calculate_level(profile.reputation_points)
    if new_level > profile.max_level_reached:
        profile.max_level_reached = new_level

    if reputation_delta < 0:
        floor_points = (profile.max_level_reached - 1) * 25
        profile.reputation_points = max(profile.reputation_points, floor_points)


def compute_vote_deltas(
    existing_value: int | None, new_value: int
) -> tuple[int, int]:
    if existing_value is None:
        if new_value == 1:
            return 1, 2
        return -1, -1
    if existing_value == new_value:
        return 0, 0
    if existing_value == 1 and new_value == -1:
        return -2, -3
    return 2, 3


class BaseVoteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [VoteThrottle]
    serializer_class = VoteInputSerializer
    target_model = None
    vote_model = None
    target_field = ""

    def post(self, request, pk):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        vote_value = int(serializer.validated_data["value"])

        with transaction.atomic():
            target = get_object_or_404(self.target_model, pk=pk)

            if target.author_id == request.user.id:
                return Response(
                    {"detail": "Self-voting is not allowed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            vote_lookup = {
                "voter": request.user,
                self.target_field: target,
            }
            try:
                vote, created = (
                    self.vote_model.objects.select_for_update().get_or_create(
                        **vote_lookup,
                        defaults={"value": vote_value},
                    )
                )
            except IntegrityError:
                vote = self.vote_model.objects.select_for_update().get(
                    **vote_lookup
                )
                created = False

            existing_value = None if created else vote.value
            score_delta, reputation_delta = compute_vote_deltas(
                existing_value,
                vote_value,
            )

            if score_delta == 0 and reputation_delta == 0:
                author_profile = Profile.objects.get(user=target.author)
                return Response(
                    {
                        "target_id": target.id,
                        "new_score": target.score,
                        "author_reputation_points": (
                            author_profile.reputation_points
                        ),
                        "author_level": author_profile.level,
                        "vote_value": vote.value,
                    },
                    status=status.HTTP_200_OK,
                )

            if score_delta != 0:
                self.target_model.objects.filter(pk=target.pk).update(
                    score=F("score") + score_delta
                )
                target.refresh_from_db(fields=["score"])

            author_profile = Profile.objects.select_for_update().get(
                user=target.author
            )
            apply_reputation_delta(author_profile, reputation_delta)
            author_profile.save(
                update_fields=["reputation_points", "max_level_reached"]
            )

            if not created:
                vote.value = vote_value
                vote.save(update_fields=["value"])

            return Response(
                {
                    "target_id": target.id,
                    "new_score": target.score,
                    "author_reputation_points": author_profile.reputation_points,
                    "author_level": author_profile.level,
                    "vote_value": vote_value,
                },
                status=status.HTTP_200_OK,
            )


class PostVoteAPIView(BaseVoteAPIView):
    target_model = Post
    vote_model = PostVote
    target_field = "post"


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
