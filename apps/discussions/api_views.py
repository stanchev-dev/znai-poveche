from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.generics import ListCreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import Profile

from .models import Comment, Post, Subject
from .serializers import (
    CommentCreateSerializer,
    CommentSerializer,
    PostCreateSerializer,
    PostDetailSerializer,
    PostListSerializer,
    SubjectSerializer,
)
from .throttles import CommentCreateThrottle, PostCreateThrottle


class PostPagination(PageNumberPagination):
    page_size = 10


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
